"""Check engine: doc_stamp -- "the documentation was updated".

The hard part of this requirement is not checking it. It is deciding what
"updated" can honestly mean to a program. Three candidates were considered:

  - **Does the doc exist / does every function have a docstring?** Real and
    deterministic, and it measures *presence*, not currency. A docstring
    written two years ago passes forever.
  - **Did the docs change in the same commit as the code?** Uses Git as the
    mechanism, which this project has refused since Spike 2: a worktree is not
    identified by its HEAD, and a project is not always its own repository.
  - **The document says which code it describes, and that claim is checked.**

The third is what this engine does, and it is Golden Thread's own mechanism
turned outward. The document carries a stamp:

    <!-- golden-thread: describes src/ sha256:<64 hex> -->

The engine recomputes the digest of the described files and compares. Equal:
whoever last touched this code re-stamped this document against it. Different:
the code moved and the document did not, and that is said with both digests.

**What this proves, stated plainly.** That someone re-stamped the document
against this exact code. Not that the prose is correct, not that it is
complete, not that they read it. `golden-thread docs stamp` takes one second
and is deliberately cheap: a gate expensive enough to resent is a gate people
route around. What the requirement removes is the *silent* case -- code
shipping with documentation nobody even claimed to have looked at since.

The stamp is a claim a person makes, in a file they own, that Golden Thread
then holds them to. It is the smallest honest thing in this space, and calling
it more than that would be exactly the sort of green tick this project exists
to refuse.
"""

import re
from pathlib import Path

from .. import subject as subject_mod
from ..errors import GoldenThreadError
from ..results import ERROR, FAIL, PASS, RuleResult
from ..subject import DIGEST_PREFIX, Subject

NAME = "doc_stamp"

STAMP = re.compile(
    r"<!--\s*golden-thread:\s*describes\s+(?P<root>\S+?)/?\s+"
    r"(?P<digest>sha256:[0-9a-f]{64})\s*-->"
)


def _document_path(rule, project: Path) -> Path:
    document = rule.params.get("document")
    if not document:
        raise GoldenThreadError(
            "rule params declare no 'document': a documentation requirement "
            "must say which document it is about"
        )
    return project / str(document)


def _described_root(rule, project: Path) -> tuple[Path, str]:
    declared = str(rule.params.get("describes", "src"))
    return project / declared, declared


def _described_globs(rule) -> list[str]:
    declared = rule.params.get("describes_globs", ["**/*.py"])
    if not isinstance(declared, list) or not declared:
        raise GoldenThreadError("rule params 'describes_globs' must be a list")
    return [str(entry) for entry in declared]


def described_paths(rule, project: Path) -> list[Path]:
    """The files the document claims to describe."""
    root, _ = _described_root(rule, project)
    paths: set[Path] = set()
    for pattern in _described_globs(rule):
        paths.update(p for p in root.glob(pattern) if p.is_file())
    return sorted(paths)


def described_digest(rule, project: Path) -> str:
    """The digest a correct stamp would carry today."""
    root, _ = _described_root(rule, project)
    paths = described_paths(rule, project)
    return subject_mod.identify(project, root, paths).digest


def expected_stamp(rule, project: Path) -> str:
    """The exact line that belongs in the document right now."""
    _, declared = _described_root(rule, project)
    return (
        f"<!-- golden-thread: describes {declared}/ "
        f"{described_digest(rule, project)} -->"
    )


def read_stamp(text: str) -> tuple[str, str] | None:
    """The (root, digest) a document claims, or None if it claims nothing."""
    match = STAMP.search(text)
    if match is None:
        return None
    return match.group("root"), match.group("digest")


def subject(rule, project: Path) -> Subject:
    """Both halves: the document, and the code it claims to describe.

    The document is part of the subject because a rewritten document is a
    different claim; the code is part of it because the claim is *about* the
    code. Either moving means the recorded verdict no longer describes what is
    in front of us, which is exactly what STALE is for.
    """
    paths = described_paths(rule, project)
    document = _document_path(rule, project)
    if document.is_file():
        paths = sorted({*paths, document})
    return subject_mod.identify(project, project, paths)


def run(rule, project: Path) -> RuleResult:
    try:
        document = _document_path(rule, project)
        _, declared_root = _described_root(rule, project)
        _described_globs(rule)
    except GoldenThreadError as exc:
        empty = subject_mod.identify(project, project, [])
        return RuleResult(status=ERROR, subject=empty, error=str(exc))

    scanned = subject(rule, project)
    relative = document.relative_to(project).as_posix()

    if not described_paths(rule, project):
        return RuleResult(
            status=ERROR,
            subject=scanned,
            error=(
                f"nothing under {declared_root}/ matches "
                f"{', '.join(_described_globs(rule))}, so there is no code for "
                f"{relative} to describe"
            ),
        )

    current = described_digest(rule, project)
    short = current[len(DIGEST_PREFIX):][:12]

    if not document.is_file():
        return RuleResult(
            status=FAIL,
            subject=scanned,
            notes=(
                f"there is no {relative}",
                f"the golden path expects this project to document "
                f"{declared_root}/ there",
            ),
        )

    stamp = read_stamp(document.read_text(encoding="utf-8"))
    if stamp is None:
        return RuleResult(
            status=FAIL,
            subject=scanned,
            notes=(
                f"{relative} carries no golden-thread stamp, so it makes no "
                "claim about which code it describes",
                f"expected a line: {expected_stamp(rule, project)}",
                "Run: golden-thread docs stamp",
            ),
        )

    stamped_root, stamped_digest = stamp
    if stamped_root.rstrip("/") != declared_root.rstrip("/"):
        return RuleResult(
            status=FAIL,
            subject=scanned,
            notes=(
                f"{relative} claims to describe {stamped_root}/, and this "
                f"requirement is about {declared_root}/",
            ),
        )

    if stamped_digest != current:
        stamped_short = stamped_digest[len(DIGEST_PREFIX):][:12]
        return RuleResult(
            status=FAIL,
            subject=scanned,
            notes=(
                f"{relative} describes {declared_root}/ at {stamped_short}",
                f"{declared_root}/ is now at {short}",
                "the code moved and the documentation did not say so",
                "read it, bring it up to date, then: golden-thread docs stamp",
            ),
        )

    return RuleResult(
        status=PASS,
        subject=scanned,
        notes=(
            f"{relative} is stamped against {declared_root}/ at {short}, which "
            "is what is there now",
            "this records that the document was re-stamped against this exact "
            "code. It is not a claim that the prose is correct: nothing here "
            "read it",
        ),
    )
