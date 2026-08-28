"""The project manifest: the attachment between a project and a Golden Thread.

Deliberately minimal, and deliberately a lockfile: it records both the ref that
was asked for and the commit that ref actually resolved to. The ref can move.
The revision cannot.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .errors import GoldenThreadError
from .paths import manifest_path

MANIFEST_VERSION = 1


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
