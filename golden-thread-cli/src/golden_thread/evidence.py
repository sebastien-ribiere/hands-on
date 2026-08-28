"""The evidence record.

One record per requirement, answering five questions and nothing more:

    requirement   which requirement?
    subject       verified on what?
    producer      by which producer?
    method        with which method?
    result        with which result?
    timestamp     when?

There is no confidence score, no signature, no central store and no evidence
taxonomy. An evidence record is a claim with its provenance attached, so that a
reader can decide for themselves whether it still applies.

Requirement and rule are one-to-one here: a rule is how a requirement is made
checkable. `requirement` holds the rule id, e.g. ARCH-001.
"""

from dataclasses import dataclass
from typing import Any

from .results import RuleResult
from .subject import Subject

EVIDENCE_VERSION = 1

PRODUCER_NAME = "golden-thread"

# How well an evidence record still describes the project in front of us.
FRESH = "FRESH"
STALE = "STALE"
NEVER = "NEVER"


@dataclass(frozen=True)
class Producer:
    name: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "version": self.version}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Producer":
        return Producer(name=data["name"], version=data["version"])

    def __str__(self) -> str:
        return f"{self.name} {self.version}"


@dataclass(frozen=True)
class Method:
    check: str
    profile: str
    policy_ref: str
    policy_revision: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "profile": self.profile,
            "policyRef": self.policy_ref,
            "policyRevision": self.policy_revision,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Method":
        return Method(
            check=data["check"],
            profile=data["profile"],
            policy_ref=data["policyRef"],
            policy_revision=data["policyRevision"],
        )

    def __str__(self) -> str:
        return (
            f"{self.check} - {self.profile} - policy {self.policy_ref} "
            f"@ {self.policy_revision[:12]}"
        )


@dataclass(frozen=True)
class Evidence:
    requirement: str
    title: str
    subject: Subject
    producer: Producer
    method: Method
    result: RuleResult
    timestamp: str
    evidence_version: int = EVIDENCE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidenceVersion": self.evidence_version,
            "requirement": self.requirement,
            "title": self.title,
            "subject": self.subject.to_dict(),
            "producer": self.producer.to_dict(),
            "method": self.method.to_dict(),
            "result": self.result.to_dict(),
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Evidence":
        subject = Subject.from_dict(data["subject"])
        return Evidence(
            requirement=data["requirement"],
            title=data.get("title", data["requirement"]),
            subject=subject,
            producer=Producer.from_dict(data["producer"]),
            method=Method.from_dict(data["method"]),
            result=RuleResult.from_dict(data["result"], subject),
            timestamp=data["timestamp"],
            evidence_version=data.get("evidenceVersion", EVIDENCE_VERSION),
        )


@dataclass(frozen=True)
class Freshness:
    """Whether an evidence record still describes what is in front of us.

    Establishing this is not producing evidence: nothing is re-checked, the
    subject is merely re-identified and the method compared to the manifest.
    """

    state: str
    reasons: tuple[str, ...] = ()
    current_subject: Subject | None = None

    @property
    def is_fresh(self) -> bool:
        return self.state == FRESH

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "reasons": list(self.reasons),
            "currentSubjectDigest": (
                self.current_subject.digest if self.current_subject else None
            ),
        }


def assess(evidence: Evidence, current: Subject, manifest) -> Freshness:
    """Compare a record against the project and the policy it is pinned to.

    Two axes, both plain equality on recorded fields:
      - the subject changed  -> the record describes code that no longer exists
      - the method changed   -> the record was produced under a different policy
    """
    reasons: list[str] = []

    if evidence.subject.digest != current.digest:
        reasons.append(
            f"the code changed: {evidence.subject.file_count} file(s) "
            f"{evidence.subject.short_digest} -> {current.file_count} file(s) "
            f"{current.short_digest}"
        )
    if evidence.method.policy_revision != manifest.revision:
        reasons.append(
            f"the Golden Thread version changed: {evidence.method.policy_ref} "
            f"@ {evidence.method.policy_revision[:12]} -> {manifest.ref} "
            f"@ {manifest.short_revision}"
        )
    if evidence.method.profile != manifest.profile:
        reasons.append(
            f"the profile changed: {evidence.method.profile} -> {manifest.profile}"
        )

    return Freshness(
        state=STALE if reasons else FRESH,
        reasons=tuple(reasons),
        current_subject=current,
    )
