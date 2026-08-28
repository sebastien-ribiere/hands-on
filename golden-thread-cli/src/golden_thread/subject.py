"""What a requirement was verified *on*.

The subject is the exact set of files a check engine read, identified by a
content digest. That is the whole invalidation mechanism: no signatures, no
timestamps of trust, no central store.

  digest = sha256 over the sorted sequence of (relative path, sha256(bytes))

It answers the three ways a subject can change -- content edited, file added,
file removed -- and it deliberately ignores everything the rule never looked
at, so editing a README does not invalidate an architecture verdict.

A Git revision is recorded when one is available, but it is *descriptive
only*. A worktree with uncommitted work is not identified by its HEAD, and a
project is not always its own repository.
"""

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

WORKTREE = "worktree"
DIGEST_PREFIX = "sha256:"


@dataclass(frozen=True)
class Subject:
    kind: str
    root: str
    file_count: int
    digest: str
    git_revision: str | None = None
    git_dirty: bool | None = None

    @property
    def short_digest(self) -> str:
        return self.digest[len(DIGEST_PREFIX):][:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "root": self.root,
            "fileCount": self.file_count,
            "digest": self.digest,
            "gitRevision": self.git_revision,
            "gitDirty": self.git_dirty,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Subject":
        return Subject(
            kind=data["kind"],
            root=data["root"],
            file_count=data["fileCount"],
            digest=data["digest"],
            git_revision=data.get("gitRevision"),
            git_dirty=data.get("gitDirty"),
        )


def digest_files(root: Path, paths: list[Path]) -> str:
    """Digest a set of files by path *and* content, order-independent."""
    outer = hashlib.sha256()
    for path in sorted(paths):
        inner = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = path.relative_to(root).as_posix()
        outer.update(f"{relative}\0{inner}\n".encode("utf-8"))
    return DIGEST_PREFIX + outer.hexdigest()


def _git(project: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project), *args],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return None
    return result.stdout if result.returncode == 0 else None


def _git_context(project: Path, root: Path) -> tuple[str | None, bool | None]:
    """HEAD and dirtiness of `root`, when the project happens to be in Git.

    Never load-bearing: both may be None and the digest still identifies the
    subject completely.
    """
    revision = _git(project, "rev-parse", "HEAD")
    if revision is None:
        return None, None
    porcelain = _git(project, "status", "--porcelain", "--", str(root))
    dirty = None if porcelain is None else bool(porcelain.strip())
    return revision.strip(), dirty


def identify(project: Path, root: Path, paths: list[Path]) -> Subject:
    """Identify the subject a check engine read.

    A root that does not exist yields an empty subject rather than an error:
    "nothing was there" is a fact about the subject, and the digest still
    changes the moment something appears.
    """
    try:
        declared = root.relative_to(project).as_posix()
    except ValueError:
        declared = str(root)
    revision, dirty = _git_context(project, root)
    return Subject(
        kind=WORKTREE,
        root=declared,
        file_count=len(paths),
        digest=digest_files(root, paths) if paths else DIGEST_PREFIX + hashlib.sha256().hexdigest(),
        git_revision=revision,
        git_dirty=dirty,
    )
