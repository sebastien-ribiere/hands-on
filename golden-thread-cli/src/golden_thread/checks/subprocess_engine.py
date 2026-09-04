"""Shared machinery for the engines that run something outside this process.

Two engines run a command the corporate policy names: `external_command` (the
exit code is the verdict) and `security_scan` (the command's report is the
verdict). What they have in common lives here.

Three rules hold for both, and each exists because of a way this could lie:

  1. **The command is an argv list, never a string.** No shell is involved, so
     there is nothing to quote, nothing to expand, and no `rm -rf $EMPTY_VAR`
     hiding behind a policy file. A rule declaring a string is refused.

  2. **The subject is declared, not inferred.** A check engine that reads the
     project's files knows exactly which ones it read. A command does not tell
     us what it opened, so the policy must say which files the requirement is
     about, as globs. Getting that wrong is a policy bug with a visible
     symptom: evidence that fails to go stale when it should, or goes stale
     constantly. It is not a bug this module can paper over by guessing.

  3. **A command that could not run is ERROR, never FAIL and never PASS.**
     A missing binary means the requirement was not checked. Reporting that as
     a failure would invent a defect; reporting it as a pass would be the
     worse of the two.

On what running a policy-declared command means: adopting a golden path is
already an agreement to run its verifications. The argv is recorded in the
evidence `method`, so what ran is in the report rather than only in a TOML file
somebody would have to go and read.
"""

import subprocess
from pathlib import Path

from .. import subject as subject_mod
from ..errors import GoldenThreadError
from ..subject import Subject

DEFAULT_TIMEOUT = 300

# Output kept on a failing command. Enough to see what happened, bounded so an
# evidence file cannot grow to the size of a test run's stdout.
MAX_OUTPUT_LINES = 20


class CommandOutcome:
    """What happened when the command ran. Never a verdict on its own."""

    def __init__(self, argv: list[str], returncode: int, stdout: str, stderr: str):
        self.argv = argv
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    @property
    def shown(self) -> str:
        return " ".join(self.argv)

    def tail(self) -> list[str]:
        """The end of what the command said, for a reader who was not there."""
        text = (self.stdout or "") + (self.stderr or "")
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        return lines[-MAX_OUTPUT_LINES:]


def command_of(rule) -> list[str]:
    """The argv this rule declares, refusing anything that is not one."""
    declared = rule.params.get("command")
    if not declared:
        raise GoldenThreadError(
            "rule params declare no 'command': an external check must say what "
            "it runs"
        )
    if isinstance(declared, str):
        raise GoldenThreadError(
            f"rule params declare 'command' as a string ({declared!r}). It must "
            "be a list of arguments: no shell is used, so a string cannot be "
            "interpreted"
        )
    if not isinstance(declared, list) or not all(isinstance(a, str) for a in declared):
        raise GoldenThreadError("rule params 'command' must be a list of strings")
    return list(declared)


def subject_globs(rule) -> list[str]:
    declared = rule.params.get("subject_globs")
    if not isinstance(declared, list) or not declared:
        raise GoldenThreadError(
            "rule params declare no 'subject_globs': a command does not report "
            "which files it read, so the policy must say which files this "
            "requirement is about"
        )
    return [str(entry) for entry in declared]


def subject(rule, project: Path) -> Subject:
    """Identify the declared subject by content, like every other engine.

    Missing files contribute nothing rather than raising: an empty subject is
    a fact about the subject, and the digest moves the moment a file appears.
    """
    root = project / str(rule.params.get("subject_root", "."))
    paths: set[Path] = set()
    for pattern in subject_globs(rule):
        paths.update(p for p in root.glob(pattern) if p.is_file())
    return subject_mod.identify(project, root, sorted(paths))


def identified(rule, project: Path) -> tuple[Subject, str]:
    """The subject, or an empty one and the reason it could not be identified.

    A rule declaring no subject is a broken rule, and a broken rule is ERROR --
    "this was not checked". Every engine here needs a Subject to put in the
    result even when it is reporting that it could not build one, so the two
    come back together rather than as an exception the caller has to remember.
    """
    try:
        return subject(rule, project), ""
    except GoldenThreadError as exc:
        return subject_mod.identify(project, project, []), str(exc)


def run_command(rule, project: Path) -> CommandOutcome:
    """Run the declared argv in the project directory.

    Raises GoldenThreadError when the command could not run at all -- the
    caller turns that into ERROR, which is what "we did not check" looks like.
    """
    argv = command_of(rule)
    timeout = int(rule.params.get("timeout_seconds", DEFAULT_TIMEOUT))
    try:
        completed = subprocess.run(
            argv,
            cwd=str(project),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise GoldenThreadError(
            f"{argv[0]!r} is not available here, so this requirement was not "
            f"checked ({exc.strerror}). The golden path expects it to be "
            "installed"
        ) from exc
    except PermissionError as exc:
        raise GoldenThreadError(f"{argv[0]!r} is not executable: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise GoldenThreadError(
            f"{' '.join(argv)} did not finish within {timeout}s, so nothing was "
            "checked"
        ) from exc
    return CommandOutcome(argv, completed.returncode, completed.stdout, completed.stderr)
