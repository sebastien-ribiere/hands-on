"""Path status: what the project's recorded evidence says about it.

  INCOMPLETE  nothing has been verified yet
  ON PATH     the last verification passed
  OFF PATH    the last verification failed

OFF PATH is a signal, not a gate. Golden Thread reports a deviation; it does
not prevent one.
"""

from dataclasses import dataclass
from pathlib import Path

from . import state
from .manifest import Manifest
from .results import FAIL, PASS, UNKNOWN

INCOMPLETE = "INCOMPLETE"
ON_PATH = "ON PATH"
OFF_PATH = "OFF PATH"


@dataclass(frozen=True)
class Status:
    manifest: Manifest
    architecture: str
    path_status: str
    verified_at: str = ""
    verified_revision: str = ""
    failing_rules: tuple = ()


def compute(project: Path, manifest: Manifest) -> Status:
    last = state.load(project)
    if last is None:
        return Status(
            manifest=manifest, architecture=UNKNOWN, path_status=INCOMPLETE
        )

    architecture = PASS if last.get("status") == PASS else FAIL
    failing = tuple(
        rule["id"]
        for rule in last.get("rules", [])
        if rule.get("status") != PASS
    )
    return Status(
        manifest=manifest,
        architecture=architecture,
        path_status=ON_PATH if architecture == PASS else OFF_PATH,
        verified_at=last.get("timestamp", ""),
        verified_revision=last.get("revision", ""),
        failing_rules=failing,
    )
