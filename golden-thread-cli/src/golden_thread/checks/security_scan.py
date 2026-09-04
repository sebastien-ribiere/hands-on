"""Check engine: security_scan.

A real security analyser runs, and its report -- not its exit code -- is the
verdict. This is the one place where the difference matters: a scanner that
found something and a scanner that crashed both exit non-zero, and treating
those alike would turn a broken tool into a security finding, or worse, a
crash into a clean bill of health.

So this engine reads the analyser's own report and copies findings out of it
unchanged: the analyser's rule id, the analyser's severity, the analyser's
words, the analyser's reference. Golden Thread adds nothing to a finding and
softens nothing. What it does add is the *policy* decision on top:

    fail_on_severity   the severity at or above which a finding is a failure
    min_confidence     the confidence below which the analyser's own report
                       says it is guessing

Both live in the corporate policy, so "MEDIUM and above fails here" is a
statement the organisation made and versioned, not a default this CLI picked.
Findings below the threshold are still recorded in the evidence, with a note
saying how many and under which threshold they were set aside. A scanner that
silently drops what it found is how a security requirement becomes decoration.

Only one report format is understood today (`format = "bandit"`), and an
unknown format is an ERROR that names what is supported. That is one branch,
not a plugin system: the day a second analyser is genuinely needed, its parser
is written then, against its real output.
"""

import json
from dataclasses import replace
from pathlib import Path

from ..errors import GoldenThreadError
from ..results import ERROR, FAIL, PASS, Finding, RuleResult
from ..subject import Subject
from . import subprocess_engine

NAME = "security_scan"

BANDIT = "bandit"
SUPPORTED_FORMATS = (BANDIT,)

# The analysers' shared vocabulary. Ordered so a threshold means something.
SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
CONFIDENCE_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

# Bandit exits 1 when it has findings and 0 when it has none. Anything else is
# the tool failing, which is not a fact about this project's code.
BANDIT_RAN = (0, 1)


def subject(rule, project: Path) -> Subject:
    return subprocess_engine.subject(rule, project)


def _rank(table: dict[str, int], value: str, default: int = 0) -> int:
    return table.get(str(value).upper(), default)


def _threshold(rule, key: str, table: dict[str, int], fallback: str) -> str:
    declared = str(rule.params.get(key, fallback)).upper()
    if declared not in table:
        raise GoldenThreadError(
            f"rule params declare {key} = {declared!r}, which is not one of "
            f"{', '.join(table)}"
        )
    return declared


def _parse_bandit(report: dict, project: Path) -> list[Finding]:
    """Copy bandit's findings out, relocating paths to the project root."""
    findings = []
    for entry in report.get("results", []):
        raw = str(entry.get("filename", ""))
        try:
            location = Path(raw).resolve().relative_to(project.resolve()).as_posix()
        except ValueError:
            location = raw
        cwe = entry.get("issue_cwe") or {}
        findings.append(
            Finding(
                file=location,
                line=int(entry.get("line_number", 0)),
                analyser=BANDIT,
                rule=str(entry.get("test_id", "?")),
                severity=str(entry.get("issue_severity", "UNKNOWN")).upper(),
                message=str(entry.get("issue_text", "")).strip(),
                reference=str(entry.get("more_info") or cwe.get("link") or ""),
            )
        )
    findings.sort(key=lambda f: (f.file, f.line, f.rule))
    return findings


def _confidence_of(report: dict, finding: Finding) -> str:
    """Bandit reports confidence per result; keep it beside its finding."""
    for entry in report.get("results", []):
        if (
            str(entry.get("test_id")) == finding.rule
            and int(entry.get("line_number", 0)) == finding.line
        ):
            return str(entry.get("issue_confidence", "HIGH")).upper()
    return "HIGH"


def run(rule, project: Path) -> RuleResult:
    scanned, broken = subprocess_engine.identified(rule, project)
    if broken:
        return RuleResult(status=ERROR, subject=scanned, error=broken)

    try:
        report_format = str(rule.params.get("format", "")).lower()
        if report_format not in SUPPORTED_FORMATS:
            raise GoldenThreadError(
                f"rule params declare format {report_format!r}. This CLI can "
                f"read: {', '.join(SUPPORTED_FORMATS)}"
            )
        fail_on = _threshold(rule, "fail_on_severity", SEVERITY_ORDER, "MEDIUM")
        min_confidence = _threshold(rule, "min_confidence", CONFIDENCE_ORDER, "LOW")
        outcome = subprocess_engine.run_command(rule, project)
    except GoldenThreadError as exc:
        return RuleResult(status=ERROR, subject=scanned, error=str(exc))

    if outcome.returncode not in BANDIT_RAN:
        return RuleResult(
            status=ERROR,
            subject=scanned,
            error=(
                f"`{outcome.shown}` exited {outcome.returncode}, which is how "
                f"{BANDIT} reports that it failed to run rather than that it "
                "found something. Nothing was scanned:\n"
                + "\n".join(outcome.tail())
            ),
        )

    try:
        report = json.loads(outcome.stdout)
    except json.JSONDecodeError as exc:
        return RuleResult(
            status=ERROR,
            subject=scanned,
            error=f"`{outcome.shown}` did not produce a readable report: {exc}",
        )

    scan_errors = report.get("errors") or []
    if scan_errors:
        # Files the analyser could not read were not scanned. Reporting PASS
        # over them would be a claim about code nothing looked at.
        details = "; ".join(
            f"{e.get('filename', '?')}: {e.get('reason', '?')}" for e in scan_errors
        )
        return RuleResult(
            status=ERROR,
            subject=scanned,
            error=f"{BANDIT} could not scan every file, so this is not a clean "
                  f"result: {details}",
        )

    if scanned.file_count == 0:
        return RuleResult(
            status=ERROR,
            subject=scanned,
            error=(
                f"no files matched "
                f"{', '.join(subprocess_engine.subject_globs(rule))}, so "
                f"`{outcome.shown}` scanned nothing. An empty scan is not a pass"
            ),
        )

    findings = _parse_bandit(report, project)
    blocking, set_aside = [], []
    for finding in findings:
        confident = _rank(CONFIDENCE_ORDER, _confidence_of(report, finding), 3)
        severe = _rank(SEVERITY_ORDER, finding.severity)
        if severe >= SEVERITY_ORDER[fail_on] and confident >= CONFIDENCE_ORDER[min_confidence]:
            blocking.append(replace(finding, blocking=True))
        else:
            set_aside.append(replace(finding, blocking=False))

    notes = [
        f"ran `{outcome.shown}` over {scanned.file_count} file(s)",
        f"this profile fails on {fail_on} and above, at {min_confidence} "
        f"confidence and above",
    ]
    if set_aside:
        notes.append(
            f"{len(set_aside)} further finding(s) recorded below that threshold, "
            "not counted as a failure here"
        )
    if not findings:
        notes.append(f"{BANDIT} reported no findings at any severity")

    return RuleResult(
        status=FAIL if blocking else PASS,
        subject=scanned,
        notes=tuple(notes),
        findings=tuple(blocking + set_aside),
    )
