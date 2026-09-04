"""Translate a `golden-thread status --json` report into short text.

This is the adapter's only judgment call, and it is a translation, not a
policy: every word here comes from a field the core already computed
(`pathStatus`, `reportedStatus`, `freshness.reasons`, `result.violations`).
No rule is evaluated here, no threshold is invented here.
"""

from typing import Any

ON_PATH = "ON PATH"
NOT_READY = "NOT READY"


def _missing_line(requirement: dict[str, Any]) -> str:
    req_id = requirement["requirement"]
    reported = requirement["reportedStatus"]

    if reported == "UNKNOWN":
        return f"{req_id} -- never verified ({requirement['title']})"

    if reported == "STALE":
        reasons = "; ".join(requirement["freshness"]["reasons"])
        return f"{req_id} -- evidence is stale: {reasons}"

    evidence = requirement.get("evidence")
    violations = evidence["result"]["violations"] if evidence else []
    if violations:
        v = violations[0]
        extra = f" (+{len(violations) - 1} more)" if len(violations) > 1 else ""
        return f"{req_id} -- {v['file']}:{v['line']} {v['sourceModule']} -> {v['targetModule']}{extra}"

    # An analyser's findings are not import-graph shaped: there is no source
    # and no target, only a location and the analyser's own rule id. Rendering
    # them through the line above would print a fabricated arrow. Only the
    # blocking ones are surfaced -- the rest were recorded below this profile's
    # threshold, and repeating them as problems would misreport the policy.
    findings = [f for f in (evidence["result"].get("findings") or []) if f["blocking"]] if evidence else []
    if findings:
        f = findings[0]
        extra = f" (+{len(findings) - 1} more)" if len(findings) > 1 else ""
        return (
            f"{req_id} -- {f['file']}:{f['line']} {f['severity']} {f['rule']} "
            f"({f['analyser']}){extra}"
        )

    error = evidence["result"].get("error") if evidence else None
    if error:
        return f"{req_id} -- could not run: {error}"

    # A requirement whose failure is not import-graph shaped -- a readiness
    # requirement, say -- explains itself in `notes`. Still the core's own
    # words: this picks which of them to show, and writes none of its own.
    notes = evidence["result"].get("notes") if evidence else None
    if notes:
        return f"{req_id} -- {'; '.join(notes)}"

    return f"{req_id} -- {reported}: {requirement['title']}"


def context_lines(report: dict[str, Any]) -> list[str]:
    """What a session should know about the golden path it opened onto."""
    gt = report["goldenThread"]
    lines = [
        f"Golden Thread {gt['ref']}",
        f"Profile: {gt['profile']}",
        f"Status: {report['pathStatus']}",
    ]
    if report["pathStatus"] != ON_PATH:
        lines += [
            f"  {_missing_line(r)}"
            for r in report["requirements"]
            if r["reportedStatus"] != "PASS"
        ]
    return lines


def deviation_lines(report: dict[str, Any] | None) -> list[str] | None:
    """A signal to show before a change, or None when there is nothing to say.

    None both when there is no Golden Thread here, and when the path is
    clean -- silence is the default; this only ever adds a message, never
    withholds the tool call that triggered it.

    NOT READY gets its own wording. "You are leaving the supported path" is
    the wrong sentence for a mission nobody agreed to yet: the code is not the
    problem, and telling a developer their edit deviates would misdescribe
    what the core actually reported.
    """
    if report is None or report["pathStatus"] == ON_PATH:
        return None
    missing = [
        _missing_line(r) for r in report["requirements"] if r["reportedStatus"] != "PASS"
    ]
    if report["pathStatus"] == NOT_READY:
        return [
            "GOLDEN THREAD -- NOT READY",
            "This work has not met its Definition of Ready.",
            *(f"Missing: {m}" for m in missing),
            "This does not stop you. It does mean nobody has agreed this yet.",
            "Run: golden-thread readiness rubric",
        ]
    return [
        "GOLDEN THREAD DEVIATION",
        "You are leaving the supported path.",
        *(f"Missing: {m}" for m in missing),
        "Run: golden-thread status",
    ]
