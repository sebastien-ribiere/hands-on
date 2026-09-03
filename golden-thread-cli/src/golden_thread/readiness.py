"""The readiness workflow: publish a rubric, receive an assessment, record a
human decision.

Three operations, and the CLI does something different in each:

    rubric    it *publishes*  -- hands out the versioned rubric the profile
                                 pins, so an assessor works from policy rather
                                 than from habit
    assess    it *validates*  -- receives a claim, checks its shape against
                                 that rubric, and records it with provenance
    approve   it *witnesses*  -- records that a named person, having seen the
                                 assessment, decided

Nothing here scores anything. This module contains no rubric text, no
heuristic, and no model: the rubric is data in the pinned corporate source, and
the assessment arrives from outside. That is what keeps the core free of any
particular agent harness while still being the thing that holds the record.

On the approval boundary, stated plainly because overstating it would be the
worst possible failure here: requiring an interactive confirmation makes
approval a *deliberate act* rather than an accident or a side effect of a
script. It is not proof that a human did it. Nothing on a developer machine can
prove that. An agent running with a terminal attached, or one that passes
`--confirm`, can record an approval; what it cannot do is record one without
naming an attestor and repeating a phrase tied to the exact text being
approved. The value is attribution and intent, not authentication.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import checks, policy, rubric as rubric_mod, source, state
from .attestation import (
    APPROVED,
    ASSESSMENT,
    HUMAN_ATTESTATION,
    REJECTED,
    REQUIRED_SECTIONS,
    Attestation,
)
from .checks import spec_readiness
from .errors import GoldenThreadError
from .rubric import Rubric
from .subject import Subject

PROVIDER_HUMAN = "human"


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Target:
    """A readiness requirement, resolved from the pinned policy."""

    def __init__(self, rule, rubric: Rubric, subject: Subject):
        self.rule = rule
        self.rubric = rubric
        self.subject = subject


def resolve(project: Path, manifest, requirement: str | None = None) -> Target:
    """Find the readiness requirement this profile enforces.

    The requirement id is never hardcoded here: the CLI asks the pinned policy
    which of its rules is a readiness rule. A profile with none has nothing to
    assess; a profile with several must be told which one.
    """
    source_root = source.ensure_available(project, manifest)
    profile = policy.load_profile(source_root, manifest.profile)
    candidates = [
        rule
        for rule in profile.rules
        if checks.kind_of(rule.check) == checks.READINESS
    ]
    if requirement is not None:
        candidates = [rule for rule in candidates if rule.id == requirement]
        if not candidates:
            raise GoldenThreadError(
                f"profile {profile.name!r} has no readiness requirement "
                f"{requirement!r}"
            )
    if not candidates:
        raise GoldenThreadError(
            f"profile {profile.name!r} enforces no readiness requirement, so "
            "there is nothing to assess"
        )
    if len(candidates) > 1:
        raise GoldenThreadError(
            f"profile {profile.name!r} has several readiness requirements "
            f"({', '.join(r.id for r in candidates)}); name one with "
            "--requirement"
        )

    rule = candidates[0]
    rubric = rubric_mod.load(
        source_root, rule.params["rubric"], str(rule.params["rubric_version"])
    )
    return Target(rule, rubric, spec_readiness.subject(rule, project))


# --- assess ------------------------------------------------------------


def _require_list(data: dict[str, Any], key: str) -> list:
    value = data.get(key)
    if not isinstance(value, list):
        raise GoldenThreadError(
            f"assessment is missing the {key!r} section, or it is not a list. "
            f"Every one of {', '.join(REQUIRED_SECTIONS)} must be present, "
            "and an empty list is a legitimate answer -- an absent one is not"
        )
    return value


def validate(data: dict[str, Any], target: Target) -> None:
    """Check a submitted assessment against the rubric it claims to follow.

    This is a real structural check, not a formality. The per-dimension scores
    must name exactly the rubric's dimensions, must each fit within what that
    dimension is worth, and must add up to the headline score. An assessment
    that reports 9/10 over dimensions summing to 6 is refused, so the number
    at the top always has an argument underneath it.
    """
    rubric = target.rubric

    assessor = data.get("assessor")
    if not isinstance(assessor, str) or not assessor.strip():
        raise GoldenThreadError(
            "assessment must name its 'assessor': a score with no author "
            "cannot be weighed"
        )

    declared_rubric = data.get("rubric")
    if declared_rubric != rubric.ref:
        raise GoldenThreadError(
            f"assessment declares rubric {declared_rubric!r}, but this profile "
            f"pins {rubric.ref!r}"
        )

    score = data.get("score")
    if not isinstance(score, int) or not 0 <= score <= rubric.scale_max:
        raise GoldenThreadError(
            f"assessment 'score' must be a whole number from 0 to "
            f"{rubric.scale_max}, got {score!r}"
        )

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, list):
        raise GoldenThreadError("assessment must carry a 'dimensions' list")

    seen: dict[str, int] = {}
    for entry in dimensions:
        if not isinstance(entry, dict) or "id" not in entry:
            raise GoldenThreadError(f"malformed dimension entry: {entry!r}")
        seen[str(entry["id"])] = entry.get("score")

    missing = sorted(rubric.dimension_ids - set(seen))
    unknown = sorted(set(seen) - rubric.dimension_ids)
    if missing or unknown:
        raise GoldenThreadError(
            f"assessment does not match rubric {rubric.ref}: "
            + (f"missing dimension(s) {', '.join(missing)}. " if missing else "")
            + (f"unknown dimension(s) {', '.join(unknown)}." if unknown else "")
        )

    for dimension in rubric.dimensions:
        awarded = seen[dimension.id]
        if not isinstance(awarded, int) or not 0 <= awarded <= dimension.points:
            raise GoldenThreadError(
                f"dimension {dimension.id!r} is worth 0 to {dimension.points} "
                f"point(s), got {awarded!r}"
            )

    total = sum(seen.values())
    if total != score:
        raise GoldenThreadError(
            f"assessment reports {score}/{rubric.scale_max} but its dimensions "
            f"add up to {total}. The headline score must be the sum of its parts"
        )

    for section in REQUIRED_SECTIONS:
        _require_list(data, section)


def record_assessment(
    project: Path, target: Target, data: dict[str, Any]
) -> Attestation:
    validate(data, target)
    attestation = Attestation(
        requirement=target.rule.id,
        kind=ASSESSMENT,
        provider=str(target.rubric.id),
        actor=str(data["assessor"]).strip(),
        rubric=target.rubric.ref,
        subject=target.subject,
        timestamp=_now(),
        payload={
            "score": data["score"],
            "dimensions": data["dimensions"],
            **{section: data[section] for section in REQUIRED_SECTIONS},
        },
    )
    state.save_attestation(project, attestation)
    return attestation


# --- approve -----------------------------------------------------------


def challenge(target: Target) -> str:
    """The phrase a human repeats to confirm.

    Tied to the subject digest, so the phrase that approves this mission does
    not approve the next one. A confirmation copied from an older session
    simply will not match.
    """
    return f"approve {target.subject.short_digest}"


def default_attestor(project: Path) -> str:
    """Who this machine says is working here. Recorded, never trusted."""
    try:
        result = subprocess.run(
            ["git", "-C", str(project), "config", "user.email"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        result = None
    if result is not None and result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    import getpass

    try:
        return getpass.getuser()
    except Exception:  # noqa: BLE001 - a machine with no user is still usable
        return "unknown"


def record_decision(
    project: Path,
    target: Target,
    decision: str,
    attestor: str,
    note: str = "",
) -> Attestation:
    attestation = Attestation(
        requirement=target.rule.id,
        kind=HUMAN_ATTESTATION,
        provider=PROVIDER_HUMAN,
        actor=attestor,
        rubric=target.rubric.ref,
        subject=target.subject,
        timestamp=_now(),
        payload={"decision": decision, "note": note},
    )
    state.save_attestation(project, attestation)
    return attestation


def confirm(target: Target, supplied: str | None) -> None:
    """Require a deliberate act before an approval is recorded.

    Refuses rather than assumes when there is no terminal and no explicit
    confirmation: a Definition of Ready that a background job can satisfy by
    accident is not one. See this module's docstring for what this does and
    does not prove.
    """
    wanted = challenge(target)
    if supplied is not None:
        if supplied.strip() != wanted:
            raise GoldenThreadError(
                f"confirmation does not match. Expected: {wanted!r}"
            )
        return

    if not sys.stdin.isatty():
        raise GoldenThreadError(
            "approval needs a person. There is no terminal attached here, so "
            "nothing can be typed.\n"
            f"To record this approval non-interactively, pass: "
            f"--confirm {wanted!r}\n"
            "Doing so records that you approved it. It does not make the "
            "approval anyone else's."
        )

    print(f"Type the phrase to confirm: {wanted}")
    try:
        typed = input("> ").strip()
    except EOFError:
        typed = ""
    if typed != wanted:
        raise GoldenThreadError("confirmation does not match. Nothing recorded")


# --- input -------------------------------------------------------------


def read_input(path: str) -> dict[str, Any]:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GoldenThreadError(f"assessment is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise GoldenThreadError("assessment must be a JSON object")
    return data


DECISIONS = (APPROVED, REJECTED)
