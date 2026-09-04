"""Records Golden Thread did not produce.

An evidence record (evidence.py) is something this CLI produced by running a
check. An *attestation* is the opposite: a claim made elsewhere -- by a model,
by a person -- and handed to Golden Thread to keep.

It is stored with the same provenance discipline and nothing more:

    requirement   which requirement it speaks to
    kind          an assessment, or a human attestation
    provider      what kind of thing made the claim
    actor         which one, exactly
    rubric        the versioned rubric it was made under
    subject       what it was made *about*, by content digest
    payload       the claim itself, whose shape the provider defines
    timestamp     when

Golden Thread does not believe an attestation because of who made it. It
records who made it, what it was made about and under which rubric, and then
applies exactly the same freshness rule it applies to everything else: a claim
about a document that has since changed no longer describes the document in
front of us, whoever made it.

An assessment is explicitly *not* a measurement. Two models asked to score the
same mission against the same rubric will disagree, and asking the same model
twice may disagree with itself. The score is one reader's opinion, recorded
with enough provenance that a human can decide what it is worth. That is why
`requires_human_approval` exists, and why no score ever satisfies a
requirement on its own.
"""

from dataclasses import dataclass, field
from typing import Any

from .subject import Subject

ATTESTATION_VERSION = 1

# The two kinds this spike knows about. Both are claims; only their author
# differs, and the difference is exactly the point.
ASSESSMENT = "assessment"
HUMAN_ATTESTATION = "human-attestation"

APPROVED = "approved"
REJECTED = "rejected"

# The two decisions a plain attestation can carry. Kept distinct from
# approved/rejected: approving an assessment somebody else produced and
# claiming something happened are different acts, and a report that called
# both "approved" would blur them.
ATTESTED = "attested"
REFUSED = "refused"

# Sections an assessment must carry. An assessment that reports only a score
# is a number without an argument, and is refused at submission.
REQUIRED_SECTIONS = (
    "facts",
    "assumptions",
    "unknowns",
    "unknownUnknowns",
    "blockers",
    "decisions",
)


@dataclass(frozen=True)
class Attestation:
    requirement: str
    kind: str
    provider: str
    actor: str
    rubric: str
    subject: Subject
    timestamp: str
    payload: dict[str, Any] = field(default_factory=dict)
    attestation_version: int = ATTESTATION_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "attestationVersion": self.attestation_version,
            "requirement": self.requirement,
            "kind": self.kind,
            "provider": self.provider,
            "actor": self.actor,
            "rubric": self.rubric,
            "subject": self.subject.to_dict(),
            "timestamp": self.timestamp,
            "payload": self.payload,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Attestation":
        return Attestation(
            requirement=data["requirement"],
            kind=data["kind"],
            provider=data["provider"],
            actor=data["actor"],
            rubric=data["rubric"],
            subject=Subject.from_dict(data["subject"]),
            timestamp=data["timestamp"],
            payload=data.get("payload", {}),
            attestation_version=data.get("attestationVersion", ATTESTATION_VERSION),
        )

    # --- assessment accessors -------------------------------------------
    # Read-only conveniences over the payload. They never compute a verdict;
    # the rule's own thresholds, which live in policy, do that.

    @property
    def score(self) -> int | None:
        value = self.payload.get("score")
        return value if isinstance(value, int) else None

    @property
    def blockers(self) -> list[str]:
        return list(self.payload.get("blockers") or [])

    @property
    def decisions(self) -> list[str]:
        return list(self.payload.get("decisions") or [])

    @property
    def decision(self) -> str:
        return str(self.payload.get("decision", ""))

    def summary(self) -> str:
        """One line, always naming who made the claim.

        A rubric is named when there is one. An attestation made under no
        rubric -- somebody stating that a thing happened -- says so rather than
        borrowing the authority of a rubric it was never measured against.
        """
        under = f" under {self.rubric}" if self.rubric else " on their own word"
        if self.kind == ASSESSMENT:
            score = "?" if self.score is None else self.score
            return f"{score}/10 by {self.actor}{under}"
        return f"{self.decision or 'no decision'} by {self.actor}{under}"


def describes(attestation: "Attestation", current: Subject) -> bool:
    """Whether this claim was made about the thing in front of us."""
    return attestation.subject.digest == current.digest
