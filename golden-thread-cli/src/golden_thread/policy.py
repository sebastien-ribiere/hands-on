"""Loading the corporate policy: catalog, profile, rules.

Everything here is data read from the pinned source tree. No project code and
no engine logic lives in this module.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import GoldenThreadError

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    check: str
    params: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    rules: list[Rule]


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GoldenThreadError(f"missing Golden Thread file: {path}")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise GoldenThreadError(f"{path} is not valid TOML: {exc}") from exc


def default_profile_name(source_root: Path) -> str:
    catalog = _load_toml(source_root / "golden-thread.toml")
    version = catalog.get("schema_version")
    if version != SCHEMA_VERSION:
        raise GoldenThreadError(
            f"Golden Thread source declares schema_version {version!r}, this "
            f"CLI understands {SCHEMA_VERSION}"
        )
    name = catalog.get("default_profile")
    if not name:
        raise GoldenThreadError(
            f"{source_root / 'golden-thread.toml'} declares no default_profile"
        )
    return name


def load_profile(source_root: Path, name: str) -> Profile:
    path = source_root / "profiles" / f"{name}.toml"
    if not path.exists():
        available = sorted(
            p.stem for p in (source_root / "profiles").glob("*.toml")
        )
        raise GoldenThreadError(
            f"unknown profile {name!r}. Available: {', '.join(available) or 'none'}"
        )
    data = _load_toml(path)
    rule_ids = data.get("rules", [])
    if not isinstance(rule_ids, list):
        raise GoldenThreadError(f"{path}: 'rules' must be a list of rule ids")

    return Profile(
        name=data.get("name", name),
        description=data.get("description", ""),
        rules=[load_rule(source_root, rule_id) for rule_id in rule_ids],
    )


def load_rule(source_root: Path, rule_id: str) -> Rule:
    path = source_root / "rules" / f"{rule_id}.toml"
    data = _load_toml(path)
    for required in ("id", "check"):
        if not data.get(required):
            raise GoldenThreadError(f"{path}: missing required field {required!r}")
    if data["id"] != rule_id:
        raise GoldenThreadError(
            f"{path}: declares id {data['id']!r} but is filed as {rule_id!r}"
        )
    return Rule(
        id=data["id"],
        title=data.get("title", rule_id),
        check=data["check"],
        params=data.get("params", {}),
        rationale=data.get("rationale", "").strip(),
    )
