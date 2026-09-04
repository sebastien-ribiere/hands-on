"""Recording a claim no tool can check.

`readiness approve` (Spike 4) witnesses a decision taken on an assessment
somebody else produced, under a versioned rubric, with a score attached. This
is the other half: a person states that something happened, with no rubric, no
score, and nothing to read but the statement in the policy.

Spike 4 deliberately chose `readiness approve` over a generic `attest`, on the
grounds that one instance is not a pattern. This is the second instance, and it
is a different act rather than a variation on the first -- so the generic
command exists now, and `readiness` is untouched: a Definition of Ready still
needs its rubric, its score and its assessment, and none of that belongs here.

The confirmation discipline is deliberately identical to Spike 4's, including
what it does not prove. The phrase is derived from the subject digest, so it
cannot be replayed against a different version of the work; the attestor is
recorded; `--confirm` exists for scripts and records the approval as the named
attestor's own. None of it demonstrates that a human typed it, and nothing on a
developer machine could.
"""

from pathlib import Path

from . import checks, policy, source, state
from .attestation import ATTESTED, HUMAN_ATTESTATION, REFUSED, Attestation
from .checks import human_attestation
from .errors import GoldenThreadError
from .readiness import PROVIDER_HUMAN, confirm_phrase, default_attestor, now
from .subject import Subject


class Target:
    """An attestable requirement, resolved from the pinned policy."""

    def __init__(self, rule, statement: str, subject: Subject):
        self.rule = rule
        self.statement = statement
        self.subject = subject


def attestable(profile) -> list:
    return [
        rule
        for rule in profile.rules
        if checks.kind_of(rule.check) == checks.ATTESTED
    ]


def resolve(project: Path, manifest, requirement: str | None = None) -> Target:
    """Find the attestable requirement, asking the policy rather than knowing it.

    No requirement id is hardcoded in this CLI. The profile decides which of
    its rules are attestable, and a profile with several must be told which
    one -- there is no "the" attestation.
    """
    source_root = source.ensure_available(project, manifest)
    profile = policy.load_profile(source_root, manifest.profile)
    candidates = attestable(profile)

    if requirement is not None:
        candidates = [rule for rule in candidates if rule.id == requirement]
        if not candidates:
            attestable_ids = ", ".join(r.id for r in attestable(profile)) or "none"
            raise GoldenThreadError(
                f"profile {profile.name!r} has no attested requirement "
                f"{requirement!r}. Attestable here: {attestable_ids}"
            )
    if not candidates:
        raise GoldenThreadError(
            f"profile {profile.name!r} enforces no attested requirement, so "
            "there is nothing to attest"
        )
    if len(candidates) > 1:
        raise GoldenThreadError(
            f"profile {profile.name!r} has several attested requirements "
            f"({', '.join(r.id for r in candidates)}); name one"
        )

    rule = candidates[0]
    return Target(
        rule,
        human_attestation.statement(rule),
        human_attestation.subject(rule, project),
    )


def challenge(target: Target) -> str:
    """The phrase a person repeats. Tied to this version of the work."""
    return f"attest {target.subject.short_digest}"


def confirm(target: Target, supplied: str | None) -> None:
    confirm_phrase(
        challenge(target),
        supplied,
        refusal=(
            "an attestation needs a person. There is no terminal attached "
            "here, so nothing can be typed."
        ),
    )


def record(
    project: Path, target: Target, decision: str, attestor: str, note: str = ""
) -> Attestation:
    attestation = Attestation(
        requirement=target.rule.id,
        kind=HUMAN_ATTESTATION,
        provider=PROVIDER_HUMAN,
        actor=attestor,
        # No rubric. Nothing measured this, and borrowing a rubric's name to
        # look more rigorous is the failure this field's emptiness prevents.
        rubric="",
        subject=target.subject,
        timestamp=now(),
        payload={"decision": decision, "note": note, "statement": target.statement},
    )
    state.save_attestation(project, attestation)
    return attestation


DECISIONS = (ATTESTED, REFUSED)


def default_actor(project: Path) -> str:
    return default_attestor(project)
