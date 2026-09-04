"""Producing evidence: running a profile's rules and recording what happened."""

from datetime import datetime, timezone
from pathlib import Path

from . import checks, policy, source
from .errors import GoldenThreadError
from .evidence import PRODUCER_NAME, Evidence, Method, Producer
from .manifest import Manifest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run(project: Path, manifest: Manifest) -> list[Evidence]:
    from . import __version__

    source_root = source.ensure_available(project, manifest)
    profile = policy.load_profile(source_root, manifest.profile)
    if not profile.rules:
        # Verifying nothing is not a pass. Silence is never green.
        raise GoldenThreadError(
            f"profile {profile.name!r} enforces no requirements, so there is "
            "nothing to verify"
        )
    producer = Producer(name=PRODUCER_NAME, version=__version__)
    timestamp = _now()

    records = []
    for rule in profile.rules:
        engine = checks.get(rule.check)
        result = engine.run(rule, project)
        records.append(
            Evidence(
                requirement=rule.id,
                title=rule.title,
                subject=result.subject,
                producer=producer,
                method=Method(
                    check=rule.check,
                    profile=profile.name,
                    policy_ref=manifest.ref,
                    policy_revision=manifest.revision,
                    # Read from the rule, not from the engine: a policy that
                    # names a command is stating part of the method, and the
                    # report has to carry what actually ran.
                    command=tuple(rule.params.get("command", []) or []),
                ),
                result=result,
                timestamp=timestamp,
            )
        )
    return records
