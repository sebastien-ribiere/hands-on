"""The last recorded verification.

`status` reports evidence, it does not produce it. That keeps the two commands
honest about which one actually ran the rules.
"""

import json
from pathlib import Path

from .paths import state_path, work_dir
from .results import VerifyResult


def save(project: Path, result: VerifyResult) -> Path:
    work_dir(project).mkdir(parents=True, exist_ok=True)
    path = state_path(project)
    path.write_text(
        json.dumps({"lastVerification": result.to_dict()}, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def load(project: Path) -> dict | None:
    path = state_path(project)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("lastVerification")
    except json.JSONDecodeError:
        return None
