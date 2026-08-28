"""Fetching and pinning the corporate Golden Thread source.

The source is a Git repository versioned by tags. We clone it into a local
cache inside the project. The cache is disposable: everything needed to
rebuild it byte-for-byte is in the manifest.
"""

import shutil
import subprocess
from pathlib import Path

from .errors import GoldenThreadError
from .paths import source_dir

CATALOG_NAME = "golden-thread.toml"


def _git(*args: str, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GoldenThreadError("git is not available on PATH") from exc
    if result.returncode != 0:
        raise GoldenThreadError(
            f"git {' '.join(args)} failed:\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def clone_at_ref(source: str, ref: str, dest: Path) -> str:
    """Clone `source` at `ref` into `dest`. Return the resolved commit SHA.

    Any existing cache at `dest` is discarded: it is a cache, not state.
    """
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # --branch accepts tags as well as branches. No --depth: it is ignored for
    # local-path clones and only produces a warning.
    _git("clone", "--quiet", "--branch", ref, source, str(dest))
    revision = _git("rev-parse", "HEAD", cwd=dest)

    if not (dest / CATALOG_NAME).exists():
        raise GoldenThreadError(
            f"{source} at {ref} does not look like a Golden Thread source: "
            f"no {CATALOG_NAME} at its root"
        )
    return revision


def checkout_revision(source: str, revision: str, dest: Path) -> None:
    """Rebuild the cache at an exact commit, as recorded in the manifest."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    _git("clone", "--quiet", source, str(dest))
    _git("checkout", "--quiet", revision, cwd=dest)


def ensure_available(project: Path, manifest) -> Path:
    """Return the local source tree, restoring it from the manifest if absent.

    A freshly cloned consumer project has a manifest but no cache. The manifest
    is enough to restore the exact reviewed policy.
    """
    dest = source_dir(project)
    if (dest / CATALOG_NAME).exists():
        return dest
    checkout_revision(manifest.source, manifest.revision, dest)
    if not (dest / CATALOG_NAME).exists():
        raise GoldenThreadError(
            f"restored {manifest.source} at {manifest.revision} but found no "
            f"{CATALOG_NAME}"
        )
    return dest
