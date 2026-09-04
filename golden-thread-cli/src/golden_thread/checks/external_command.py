"""Check engine: external_command.

The requirement is satisfied when a command the policy names exits zero. This
is how "the tests pass" becomes a Golden Thread requirement without the CLI
ever learning what a test is.

What this engine claims, exactly: a named command was run against a named set
of files, and it exited with a given code. It does not claim the tests are
good, that they cover anything, or that a passing suite means working software.
An empty test suite exits zero, and this engine will report PASS -- because
that is what happened. Requiring that the suite be meaningful is a different
requirement, and it would need a different engine rather than a stricter
reading of this one's exit code.

The exit code is the whole verdict on purpose. A test runner's output format is
its own business and changes between versions; its exit code is the one part
of its interface every runner in every language agrees on.
"""

from pathlib import Path

from ..errors import GoldenThreadError
from ..results import ERROR, FAIL, PASS, RuleResult
from ..subject import Subject
from . import subprocess_engine

NAME = "external_command"


def subject(rule, project: Path) -> Subject:
    return subprocess_engine.subject(rule, project)


def run(rule, project: Path) -> RuleResult:
    scanned, broken = subprocess_engine.identified(rule, project)
    if broken:
        return RuleResult(status=ERROR, subject=scanned, error=broken)

    try:
        outcome = subprocess_engine.run_command(rule, project)
    except GoldenThreadError as exc:
        return RuleResult(status=ERROR, subject=scanned, error=str(exc))

    if scanned.file_count == 0:
        # The command may well have exited zero. It had nothing to run against,
        # and a pass over nothing is the failure mode this project refuses.
        return RuleResult(
            status=ERROR,
            subject=scanned,
            error=(
                f"no files matched {', '.join(subprocess_engine.subject_globs(rule))}, "
                f"so `{outcome.shown}` ran against nothing. An exit code over an "
                "empty subject is not evidence"
            ),
        )

    notes = [f"ran `{outcome.shown}` in {scanned.root}/, exit {outcome.returncode}"]
    if outcome.returncode != 0:
        notes.append("the command reported:")
        notes.extend(f"  {line}" for line in outcome.tail())

    return RuleResult(
        status=PASS if outcome.returncode == 0 else FAIL,
        subject=scanned,
        notes=tuple(notes),
    )
