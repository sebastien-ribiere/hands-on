"""Running a profile's rules against a project."""

from datetime import datetime, timezone
from pathlib import Path

from . import checks, policy, source
from .manifest import Manifest
from .results import VerifyResult


def run(project: Path, manifest: Manifest) -> VerifyResult:
    source_root = source.ensure_available(project, manifest)
    profile = policy.load_profile(source_root, manifest.profile)

    results = []
    for rule in profile.rules:
        engine = checks.get(rule.check)
        results.append(engine(rule, project))

    return VerifyResult(
        profile=profile.name,
        ref=manifest.ref,
        revision=manifest.revision,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        rules=results,
    )
