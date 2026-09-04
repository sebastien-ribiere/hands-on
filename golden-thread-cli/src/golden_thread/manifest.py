"""The project manifest: the attachment between a project and a Golden Thread.

Deliberately minimal, and deliberately a lockfile: it records both the ref that
was asked for and the commit that ref actually resolved to. The ref can move.
The revision cannot.

`source` is stored exactly as it was given. A forge URL is the normal case. A
*relative* path is resolved against the project directory, which is what lets a
manifest be committed at all: an absolute path is specific to one machine, and
a manifest nobody can commit cannot pin anything for anybody else -- least of
all for a CI runner, which has no developer to run `init` for it.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import GoldenThreadError
from .paths import manifest_path

MANIFEST_VERSION = 1

# Anything with a scheme, or a scp-style Git address, is left alone. Everything
# else is treated as a path, and a relative one is relative to the project.
_REMOTE_MARKERS = ("://", "git@", "ssh://")


def resolve_source(source: str, project: Path) -> str:
    if any(marker in source for marker in _REMOTE_MARKERS):
        return source
    path = Path(source)
    if path.is_absolute():
        return str(path)
    return str((project / path).resolve())


@dataclass(frozen=True)
class Manifest:
    source: str
    ref: str
    revision: str
    profile: str
    manifest_version: int = MANIFEST_VERSION

    def to_json(self) -> str:
        data = {
            "manifestVersion": self.manifest_version,
            "source": self.source,
            "ref": self.ref,
            "revision": self.revision,
            "profile": self.profile,
        }
        return json.dumps(data, indent=2) + "\n"

    @property
    def short_revision(self) -> str:
        return self.revision[:12]

    def resolved_source(self, project: Path) -> str:
        """Where to actually fetch from, for this project on this machine.

        A URL, or an absolute path, is returned unchanged. A relative path is
        resolved against the project directory rather than the working
        directory: `golden-thread -C somewhere status` must mean the same thing
        as running it from inside `somewhere`.
        """
        return resolve_source(self.source, project)


def write(project: Path, manifest: Manifest) -> Path:
    path = manifest_path(project)
    path.write_text(manifest.to_json(), encoding="utf-8")
    return path


def read(project: Path) -> Manifest:
    path = manifest_path(project)
    if not path.exists():
        raise GoldenThreadError(
            f"no Golden Thread manifest at {path}\n"
            "run: golden-thread init --source <repo> --ref <tag>"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GoldenThreadError(f"manifest {path} is not valid JSON: {exc}") from exc

    missing = [k for k in ("source", "ref", "revision", "profile") if not data.get(k)]
    if missing:
        raise GoldenThreadError(
            f"manifest {path} is missing required field(s): {', '.join(missing)}"
        )

    version = data.get("manifestVersion", MANIFEST_VERSION)
    if version != MANIFEST_VERSION:
        raise GoldenThreadError(
            f"manifest {path} has version {version}, this CLI understands "
            f"version {MANIFEST_VERSION}"
        )

    return Manifest(
        source=data["source"],
        ref=data["ref"],
        revision=data["revision"],
        profile=data["profile"],
        manifest_version=version,
    )


def exists(project: Path) -> bool:
    return manifest_path(project).exists()
