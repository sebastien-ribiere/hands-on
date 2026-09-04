"""Check engine: human_attestation.

Some requirements cannot be verified by anything, ever, and the honest move is
to say so in the mechanism rather than to approximate them with a check that
looks rigorous. This engine holds those. It runs no analysis and reads no code:
it looks for a claim a named person made about a named subject, and reports
whether one is on record and still applies.

The Academy's Definition of Done requires that cookies were prepared and shared
with the team. That is deliberately absurd, and it is doing real work in this
design: it is an organisational rule that no scanner, no test suite and no
model can establish. Every organisation has some -- the demo was walked
through with the right people, the on-call rota was told, the customer was
warned before the migration. A tool that could only express what it could
compute would quietly push those out of the Definition of Done, and the ones
that fall out are rarely the unimportant ones.

So the requirement stays in the profile, with the same standing as the
architecture rule, and it is satisfied by an attestation carrying a name. What
Golden Thread guarantees is narrow and worth stating: that somebody said it,
who they were, what exactly they were shown when they said it, and that they
said it about *this* version of the work. Whether it was true is between them
and the team.

Kind `attested` rather than `code`: the engine reaches no verdict of its own.
Unlike a readiness requirement, though, an unmet one is an ordinary OFF PATH --
it is a piece of the Definition of Done that has not been done, not a statement
that the work was never agreed.
"""

from pathlib import Path

from .. import attestation as attestation_mod
from .. import state
from ..attestation import ATTESTED, HUMAN_ATTESTATION
from ..errors import GoldenThreadError
from ..results import ERROR, FAIL, PASS, RuleResult
from ..subject import Subject
from . import subprocess_engine

NAME = "human_attestation"


def statement(rule) -> str:
    """What the person is being asked to attest, in the policy's own words."""
    declared = rule.params.get("statement")
    if not declared or not str(declared).strip():
        raise GoldenThreadError(
            "rule params declare no 'statement': an attested requirement must "
            "say, in words, what a person is being asked to claim"
        )
    return str(declared).strip()


def subject(rule, project: Path) -> Subject:
    """What an attestation here is tied to.

    Declared as globs by the policy, exactly as for a command: an attestation
    is made about a version of the work, and the work has to be identified for
    the claim to expire when it changes.
    """
    return subprocess_engine.subject(rule, project)


def run(rule, project: Path) -> RuleResult:
    scanned, broken = subprocess_engine.identified(rule, project)
    if broken:
        return RuleResult(status=ERROR, subject=scanned, error=broken)

    try:
        claimed = statement(rule)
    except GoldenThreadError as exc:
        return RuleResult(status=ERROR, subject=scanned, error=str(exc))

    recorded = state.latest_attestation(project, rule.id, HUMAN_ATTESTATION)
    supporting = (recorded,) if recorded is not None else ()
    notes = [f"the claim: {claimed}"]

    if recorded is None:
        notes.append(
            "nobody has attested this, and nothing here can attest it on their "
            "behalf"
        )
        notes.append(f"Run: golden-thread attest {rule.id}")
        return RuleResult(
            status=FAIL, subject=scanned, notes=tuple(notes), supporting=supporting
        )

    if not attestation_mod.describes(recorded, scanned):
        notes.append(
            f"{recorded.actor} attested this about a different version of the "
            f"work ({recorded.subject.file_count} file(s) "
            f"{recorded.subject.short_digest} -> {scanned.file_count} file(s) "
            f"{scanned.short_digest})"
        )
        notes.append("the work moved on; the claim did not move with it")
        return RuleResult(
            status=FAIL, subject=scanned, notes=tuple(notes), supporting=supporting
        )

    if recorded.decision != ATTESTED:
        note = recorded.payload.get("note", "")
        notes.append(
            f"{recorded.actor} recorded '{recorded.decision}'"
            + (f": {note}" if note else "")
        )
        return RuleResult(
            status=FAIL, subject=scanned, notes=tuple(notes), supporting=supporting
        )

    note = recorded.payload.get("note", "")
    notes.append(f"attested by {recorded.actor}" + (f": {note}" if note else ""))
    notes.append(
        "recorded on their word alone. Golden Thread verified that somebody "
        "said it, not that it happened"
    )
    return RuleResult(
        status=PASS, subject=scanned, notes=tuple(notes), supporting=supporting
    )
