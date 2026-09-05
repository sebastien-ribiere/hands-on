"""The golden-thread command line.

Every command has a human-readable form and a `--json` form carrying the same
evidence. Neither ever reports a bare verdict: a status is always shown with
the subject, producer and method it came from.

Exit codes:
  0  ON PATH, or INCOMPLETE (nothing verified yet)
  1  OFF PATH: a requirement failed on evidence that still applies
  2  the command itself could not run
  3  STALE: evidence exists but no longer describes this project
  4  NOT READY: a readiness requirement is not satisfied
"""

import argparse
import os
import shlex
import sys
from pathlib import Path

from . import manifest as manifest_mod
from . import (
    attest as attest_mod,
    docs as docs_mod,
    policy,
    readiness,
    report,
    source,
    state,
    status as status_mod,
    verify,
)
from .attestation import APPROVED, ASSESSMENT, ATTESTED, REFUSED, REJECTED
from .errors import GoldenThreadError
from .paths import WORK_DIR_NAME
from .results import ERROR, FAIL

LABEL_WIDTH = 14
INDENT = " " * 7


def _line(label: str, value: str) -> str:
    return f"{label.ljust(LABEL_WIDTH)}{value}"


def _next_command(args: argparse.Namespace, action: str) -> str:
    """Render a follow-up command that preserves the selected project."""
    executable = os.environ.get("GOLDEN_THREAD_SELF", "golden-thread")
    parts = [shlex.quote(executable)]
    if args.project != ".":
        parts.extend(["-C", shlex.quote(args.project)])
    parts.append(action)
    return " ".join(parts)


def _ensure_gitignored(project: Path) -> None:
    """Keep the cache and recorded evidence out of the consumer's history."""
    entry = f"{WORK_DIR_NAME}/"
    gitignore = project / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if entry in existing.split():
        return
    prefix = "" if existing.endswith("\n") or not existing else "\n"
    gitignore.write_text(
        f"{existing}{prefix}# Golden Thread cache and recorded evidence\n{entry}\n",
        encoding="utf-8",
    )


def _git_note(subject) -> str:
    """Context, never the mechanism: the digest is what decides."""
    if not subject.git_revision:
        return ""
    dirty = ", dirty" if subject.git_dirty else ""
    return f"   git {subject.git_revision[:12]}{dirty}"


def _describe(subject) -> str:
    return f"{subject.file_count} file(s) sha256:{subject.short_digest}"


def _print_provenance(entry) -> None:
    """Where a claim comes from. Printed for every requirement, always."""
    evidence = entry.evidence
    current = entry.freshness.current_subject
    subject = evidence.subject

    if entry.reported_status == status_mod.STALE:
        print(
            f"{INDENT}subject   recorded {_describe(subject)}{_git_note(subject)}"
        )
        if current is not None:
            print(
                f"{INDENT}          current  {_describe(current)}{_git_note(current)}"
            )
    else:
        print(
            f"{INDENT}subject   {subject.root}/ - {_describe(subject)}"
            f"{_git_note(subject)}"
        )
    # A requirement satisfied by claims made elsewhere never appears without
    # them: the assessment and the human decision are part of the provenance,
    # not a detail behind a --verbose flag.
    for claim in evidence.result.supporting:
        print(f"{INDENT}rests on  {claim.kind}: {claim.summary()}")
    print(f"{INDENT}method    {evidence.method}")
    print(f"{INDENT}tool      {evidence.producer}")
    print(f"{INDENT}recorded  {evidence.timestamp}")


def _print_entry(entry) -> None:
    reported = entry.reported_status
    print(f"{reported.ljust(6)} {entry.requirement}  {entry.title}")

    if entry.evidence is None:
        print(f"{INDENT}never verified")
        print()
        return

    if reported == status_mod.STALE:
        print(
            f"{INDENT}recorded {entry.evidence.result.status} no longer applies:"
        )
        for reason in entry.freshness.reasons:
            print(f"{INDENT}  - {reason}")
    else:
        if reported == ERROR:
            print(f"{INDENT}could not run: {entry.evidence.result.error}")
        for violation in entry.evidence.result.violations:
            print(f"{INDENT}{violation.file}:{violation.line}")
            print(f"{INDENT}  {violation.source_module} -> {violation.target_module}")
            print(f"{INDENT}  {violation.reason}")
        # An analyser's findings, in the analyser's own terms. The severity and
        # the rule id are the tool's, not ours, and the reference is printed so
        # a reader can go and disagree with it.
        for finding in entry.evidence.result.findings:
            below = "" if finding.blocking else "   [below this profile's threshold]"
            print(f"{INDENT}{finding.file}:{finding.line}{below}")
            print(
                f"{INDENT}  {finding.severity} {finding.rule} "
                f"({finding.analyser}): {finding.message}"
            )
            if finding.reference:
                print(f"{INDENT}  {finding.reference}")
        # Printed for PASS as much as for FAIL: a verdict is never shown
        # without the reason it is that verdict.
        for note in entry.evidence.result.notes:
            print(f"{INDENT}- {note}")

    _print_provenance(entry)
    print()


def _print_trailer(status) -> None:
    print(f"PATH STATUS   {status.path_status}")

    if status.path_status == status_mod.INCOMPLETE:
        print()
        print("Nothing verified yet. Run: golden-thread verify")
    elif status.path_status == status_mod.STALE:
        print()
        print("Evidence exists but no longer describes this project, so it is")
        print("not shown as a verdict. Run: golden-thread verify")
    elif status.path_status == status_mod.NOT_READY:
        print()
        print("A readiness requirement is not satisfied: this work was not agreed")
        print("before it started. Like every other Golden Thread signal, it is a")
        print("signal -- nothing here stops you writing code. It states that the")
        print("Definition of Ready has not been met, and by whose account.")
        print("Next          golden-thread readiness rubric")
    elif status.path_status == status_mod.OFF_PATH:
        failing = [
            e
            for e in status.entries
            if e.evidence is not None and e.reported_status in (FAIL, ERROR)
        ]
        # Counted across both lists, and only what this profile treats as a
        # failure. A requirement can fail with nothing located in the code at
        # all -- nobody made the cookies -- and reporting "0 violations" under
        # an OFF PATH headline is the kind of arithmetic that makes a reader
        # stop trusting the rest of the report.
        located = sum(
            len(e.evidence.result.violations)
            + len([f for f in e.evidence.result.findings if f.blocking])
            for e in failing
        )
        print()
        print(
            f"{len(failing)} requirement(s) not satisfied, {located} located in "
            "the code."
        )
        print(
            "This is a signal, not a block: you may stay off path deliberately, "
            "but the"
        )
        print("deviation is now explicit.")


def _render(title: str, status) -> None:
    manifest = status.manifest
    print(title)
    print(_line("Policy ref", manifest.ref))
    print(_line("Policy SHA", manifest.short_revision))
    print(_line("Profile", manifest.profile))
    print()
    for entry in status.entries:
        _print_entry(entry)
    _print_trailer(status)


def _emit(command: str, title: str, status, as_json: bool) -> int:
    if as_json:
        print(report.dumps(command, status))
    else:
        _render(title, status)
    return status.exit_code


def cmd_init(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    if not project.is_dir():
        raise GoldenThreadError(f"project directory does not exist: {project}")

    dest = project / WORK_DIR_NAME / "source"
    # Fetched from the resolved location, recorded exactly as it was given: a
    # relative source stays relative, so the manifest can be committed.
    revision = source.clone_at_ref(
        manifest_mod.resolve_source(args.source, project), args.ref, dest
    )
    profile_name = args.profile or policy.default_profile_name(dest)
    # Fail at init, not at first verify, if the profile does not exist.
    profile = policy.load_profile(dest, profile_name)

    written = manifest_mod.write(
        project,
        manifest_mod.Manifest(
            source=args.source,
            ref=args.ref,
            revision=revision,
            profile=profile.name,
        ),
    )
    _ensure_gitignored(project)

    print("Golden Thread attached")
    print(_line("Source", args.source))
    print(_line("Policy ref", args.ref))
    print(_line("Policy SHA", revision))
    print(_line("Profile", profile.name))
    print(_line("Requirements", ", ".join(r.id for r in profile.rules) or "none"))
    print()
    print(f"Manifest      {written.relative_to(project)}")
    print(f"Next          {_next_command(args, 'verify')}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    manifest = manifest_mod.read(project)
    return _emit("status", "Golden Thread", status_mod.compute(project, manifest), args.json)


def cmd_verify(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    manifest = manifest_mod.read(project)
    records = verify.run(project, manifest)
    state.save(project, records)
    current = status_mod.from_records(manifest, records)
    return _emit("verify", "Golden Thread verify", current, args.json)


def _readiness_target(args: argparse.Namespace):
    project = Path(args.project).resolve()
    manifest = manifest_mod.read(project)
    return project, readiness.resolve(project, manifest, args.requirement)


def cmd_readiness_rubric(args: argparse.Namespace) -> int:
    """Publish the rubric, so an assessment is made against policy, not habit."""
    _, target = _readiness_target(args)
    rubric = target.rubric

    if args.json:
        print(
            report.json_dumps(
                {
                    "requirement": target.rule.id,
                    "title": target.rule.title,
                    "rubric": rubric.ref,
                    "rubricTitle": rubric.title,
                    "scaleMax": rubric.scale_max,
                    "caveat": rubric.caveat,
                    "thresholds": {
                        "minScore": target.rule.params.get("min_score", 8),
                        "maxBlockers": target.rule.params.get("max_blockers", 0),
                        "requiresHumanApproval": target.rule.params.get(
                            "requires_human_approval", True
                        ),
                    },
                    "subject": target.subject.to_dict(),
                    "subjectFiles": target.rule.params.get("subject_files", []),
                    "dimensions": [
                        {
                            "id": d.id,
                            "title": d.title,
                            "points": d.points,
                            "asks": d.asks,
                        }
                        for d in rubric.dimensions
                    ],
                    "requiredSections": list(readiness.REQUIRED_SECTIONS),
                }
            )
        )
        return 0

    print(f"{target.rule.id}  {target.rule.title}")
    print(_line("Rubric", f"{rubric.ref}  {rubric.title}"))
    print(_line("Subject", f"{_describe(target.subject)}"))
    print()
    for dimension in rubric.dimensions:
        print(f"  {dimension.id}  ({dimension.points} pt)  {dimension.title}")
        if dimension.asks:
            for line in dimension.asks.splitlines():
                print(f"      {line}")
    print()
    print(_line("Threshold", f"score >= {target.rule.params.get('min_score', 8)}"
                             f" / {rubric.scale_max}"))
    print(_line("Blockers", f"at most {target.rule.params.get('max_blockers', 0)}"))
    print(_line("Approval", "a human decision is required"
                if target.rule.params.get("requires_human_approval", True)
                else "not required"))
    print()
    print("Required sections in an assessment:")
    print(f"  {', '.join(readiness.REQUIRED_SECTIONS)}")
    if rubric.caveat:
        print()
        for line in rubric.caveat.splitlines():
            print(line)
    return 0


def cmd_readiness_assess(args: argparse.Namespace) -> int:
    """Receive an assessment. The CLI validates its shape; it never scores."""
    project, target = _readiness_target(args)
    data = readiness.read_input(args.input)
    recorded = readiness.record_assessment(project, target, data)

    print(f"{target.rule.id}  assessment recorded")
    print(_line("Score", f"{recorded.score}/{target.rubric.scale_max}"))
    print(_line("Rubric", recorded.rubric))
    print(_line("Assessor", recorded.actor))
    print(_line("Subject", _describe(recorded.subject)))
    for section in ("blockers", "decisions"):
        items = recorded.payload.get(section) or []
        if items:
            print()
            print(f"{section.capitalize()} ({len(items)}):")
            for index, item in enumerate(items, 1):
                print(f"  {index}. {item}")
    print()
    print("This is one reader's assessment of a document, not a measurement.")
    print("It satisfies nothing on its own.")
    print("Next          golden-thread verify")
    return 0


def cmd_readiness_approve(args: argparse.Namespace) -> int:
    """Record a human decision, having shown that human what they are deciding."""
    project, target = _readiness_target(args)
    decision = REJECTED if args.reject else APPROVED

    assessment = state.latest_attestation(project, target.rule.id, ASSESSMENT)
    if assessment is None:
        raise GoldenThreadError(
            "there is no readiness assessment to decide on. "
            "Run: golden-thread readiness rubric"
        )
    if assessment.subject.digest != target.subject.digest:
        raise GoldenThreadError(
            "the recorded assessment was made about a different version of the "
            f"mission ({assessment.subject.short_digest} -> "
            f"{target.subject.short_digest}). Re-assess before deciding"
        )
    if assessment.rubric != target.rubric.ref:
        raise GoldenThreadError(
            f"the recorded assessment was made under rubric {assessment.rubric}, "
            f"and this profile now pins {target.rubric.ref}. Re-assess first"
        )

    attestor = args.attestor or readiness.default_attestor(project)

    print(f"{target.rule.id}  {target.rule.title}")
    print(_line("Assessment", f"{assessment.score}/{target.rubric.scale_max} "
                              f"by {assessment.actor}"))
    print(_line("Rubric", assessment.rubric))
    print(_line("Subject", _describe(target.subject)))
    for section in ("blockers", "decisions"):
        items = assessment.payload.get(section) or []
        for index, item in enumerate(items, 1):
            print(f"  {section[:-1]} {index}. {item}")
    print(_line("Attestor", attestor))
    print()
    print(f"This records that YOU {decision} this mission, on your own reading.")
    print("The score above is an opinion; it has approved nothing.")
    print()

    readiness.confirm(target, args.confirm)
    recorded = readiness.record_decision(
        project, target, decision, attestor, args.note or ""
    )

    print()
    print(f"{target.rule.id}  human attestation recorded")
    print(_line("Decision", recorded.decision))
    print(_line("Attestor", recorded.actor))
    print("Next          golden-thread verify")
    return 0


def cmd_attest(args: argparse.Namespace) -> int:
    """Record a claim nothing can check, having shown what is being claimed."""
    project = Path(args.project).resolve()
    manifest = manifest_mod.read(project)
    target = attest_mod.resolve(project, manifest, args.requirement)
    decision = REFUSED if args.refuse else ATTESTED
    attestor = args.attestor or attest_mod.default_actor(project)

    print(f"{target.rule.id}  {target.rule.title}")
    print(_line("Claim", target.statement))
    print(_line("Subject", _describe(target.subject)))
    print(_line("Attestor", attestor))

    if args.show:
        # What would be asked, without asking it. For a script that has to
        # supply --confirm, and for anyone who wants to see the claim before
        # deciding whether they are willing to make it.
        print(_line("Confirm with", f"--confirm {attest_mod.challenge(target)!r}"))
        print()
        print("Nothing was recorded.")
        return 0

    print()
    print(f"This records that YOU {decision} this, on your own account.")
    print("Nothing here checked it. Nothing here can: that is why this")
    print("requirement is satisfied by a name rather than by a verdict.")
    print()

    attest_mod.confirm(target, args.confirm)
    recorded = attest_mod.record(
        project, target, decision, attestor, args.note or ""
    )

    print()
    print(f"{target.rule.id}  attestation recorded")
    print(_line("Decision", recorded.decision))
    print(_line("Attestor", recorded.actor))
    print("Next          golden-thread verify")
    return 0


def cmd_docs_stamp(args: argparse.Namespace) -> int:
    """Stamp a document with the digest of the code it describes."""
    project = Path(args.project).resolve()
    manifest = manifest_mod.read(project)
    target = docs_mod.resolve(project, manifest, args.requirement)
    line, changed = docs_mod.stamp(project, target)

    relative = target.document.relative_to(project).as_posix()
    print(f"{target.rule.id}  {'stamped' if changed else 'already current'}")
    print(_line("Document", relative))
    print(_line("Describes", f"{target.describes}/"))
    print(_line("Stamp", line))
    print()
    print("This records that this document was stamped against this exact")
    print("code. It is not a claim that the documentation is correct: nothing")
    print("here read it, and nothing here could tell you if it were wrong.")
    print("Next          golden-thread verify")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="golden-thread",
        description="Attach a project to a versioned Golden Thread and verify it.",
    )
    parser.add_argument(
        "-C",
        "--project",
        default=".",
        help="project directory (default: current directory)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="attach this project to a Golden Thread")
    init.add_argument("--source", required=True, help="Git repository of the Golden Thread")
    init.add_argument("--ref", required=True, help="tag or branch to pin, e.g. v0.1.0")
    init.add_argument("--profile", help="profile to use (default: the source's own)")
    init.set_defaults(func=cmd_init)

    status = subparsers.add_parser("status", help="report the evidence on record")
    status.add_argument("--json", action="store_true", help="machine-readable report")
    status.set_defaults(func=cmd_status)

    verify_cmd = subparsers.add_parser("verify", help="produce evidence for the profile's requirements")
    verify_cmd.add_argument("--json", action="store_true", help="machine-readable report")
    verify_cmd.set_defaults(func=cmd_verify)

    readiness_cmd = subparsers.add_parser(
        "readiness",
        help="the Definition of Ready: publish the rubric, record an "
             "assessment, record a human decision",
    )
    readiness_sub = readiness_cmd.add_subparsers(dest="readiness_command", required=True)

    def _shared(sub):
        sub.add_argument(
            "--requirement",
            help="which readiness requirement (only needed if the profile has "
                 "more than one)",
        )
        return sub

    rubric_cmd = _shared(readiness_sub.add_parser(
        "rubric", help="print the versioned rubric this profile pins"
    ))
    rubric_cmd.add_argument("--json", action="store_true", help="machine-readable rubric")
    rubric_cmd.set_defaults(func=cmd_readiness_rubric)

    assess_cmd = _shared(readiness_sub.add_parser(
        "assess", help="record an assessment produced against the rubric"
    ))
    assess_cmd.add_argument(
        "--input", required=True, help="JSON assessment file, or - for stdin"
    )
    assess_cmd.set_defaults(func=cmd_readiness_assess)

    approve_cmd = _shared(readiness_sub.add_parser(
        "approve", help="record a human decision on the recorded assessment"
    ))
    approve_cmd.add_argument("--attestor", help="who is deciding (default: git user.email)")
    approve_cmd.add_argument("--note", help="why, in the attestor's own words")
    approve_cmd.add_argument(
        "--reject",
        action="store_true",
        help="record a refusal rather than an approval",
    )
    approve_cmd.add_argument(
        "--confirm",
        help="the confirmation phrase, for use where no terminal is attached. "
             "Recording an approval this way still records it as yours",
    )
    approve_cmd.set_defaults(func=cmd_readiness_approve)

    attest_cmd = subparsers.add_parser(
        "attest",
        help="record a claim no tool can check, for a requirement satisfied by "
             "a person's word",
    )
    attest_cmd.add_argument(
        "requirement",
        nargs="?",
        help="which requirement (only needed if the profile has more than one)",
    )
    attest_cmd.add_argument("--attestor", help="who is claiming (default: git user.email)")
    attest_cmd.add_argument("--note", help="anything worth recording alongside it")
    attest_cmd.add_argument(
        "--refuse",
        action="store_true",
        help="record that this is NOT the case, rather than that it is",
    )
    attest_cmd.add_argument(
        "--confirm",
        help="the confirmation phrase, for use where no terminal is attached. "
             "Recording an attestation this way still records it as yours",
    )
    attest_cmd.add_argument(
        "--show",
        action="store_true",
        help="print the claim and the confirmation phrase, and record nothing",
    )
    attest_cmd.set_defaults(func=cmd_attest)

    docs_cmd = subparsers.add_parser(
        "docs", help="the documentation requirement: stamp a document"
    )
    docs_sub = docs_cmd.add_subparsers(dest="docs_command", required=True)
    stamp_cmd = docs_sub.add_parser(
        "stamp", help="record which version of the code this document describes"
    )
    stamp_cmd.add_argument(
        "--requirement",
        help="which documentation requirement (only needed if the profile has "
             "more than one)",
    )
    stamp_cmd.set_defaults(func=cmd_docs_stamp)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GoldenThreadError as exc:
        print(f"golden-thread: {exc}", file=sys.stderr)
        return 2
