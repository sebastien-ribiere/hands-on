"""What a check engine returns.

Deliberately concrete: a rule passed, failed, or could not run, a failure
carries the exact locations that caused it, and the result carries the subject
it was produced from. No generic evidence taxonomy.

Three fields are additive and default to empty, so a record written before they
existed still loads unchanged:

  notes       why this result is what it is, in words, for requirements whose
              failures are not import-graph shaped ("assessed at 7/10, below
              the 8 this profile requires"). Printed for PASS as well as FAIL:
              a verdict without its reason is exactly what this project
              refuses to emit.
  supporting  the attestations this result rests on. A requirement satisfied
              by a model's assessment and a person's approval carries both
              records here, so the claim can never be read without them.
  findings    what an external analyser reported, in the analyser's own terms.

`violations` and `findings` are deliberately two lists rather than one. A
violation is import-graph shaped -- this module depends on that one, and it may
not -- and every reader of the report, adapters included, renders it as
`source -> target`. A security finding has no source and no target: it has a
location, the analyser's own rule id, a severity that analyser assigned, and a
reference. Squeezing one into the other would mean inventing a `targetModule`
for a hardcoded password, and a reader would be shown a fabricated field.
"""

from dataclasses import dataclass, field
from typing import Any

from .attestation import Attestation
from .subject import Subject

PASS = "PASS"
FAIL = "FAIL"
ERROR = "ERROR"
UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    source_module: str
    target_module: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "sourceModule": self.source_module,
            "targetModule": self.target_module,
            "reason": self.reason,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Violation":
        return Violation(
            file=data["file"],
            line=data["line"],
            source_module=data["sourceModule"],
            target_module=data["targetModule"],
            reason=data["reason"],
        )


@dataclass(frozen=True)
class Finding:
    """What an external analyser reported, in that analyser's own terms.

    Golden Thread never restates a finding in words of its own, and never
    assigns it a severity. `analyser`, `rule` and `severity` are copied out of
    the tool's report unchanged, so a reader can go back to the tool and check.
    `reference` is whatever the tool published to justify itself -- a CWE page,
    its own documentation -- and is empty when the tool gave none.

    `blocking` is the one field Golden Thread adds, and it is not the
    analyser's opinion: it says whether *this profile's* threshold makes this
    finding a failure. Findings below the threshold are recorded rather than
    dropped, so a reader can see everything the analyser said and see where the
    organisation drew its line -- but a report that listed both alike would
    make a team look worse than the policy actually says they are.
    """

    file: str
    line: int
    analyser: str
    rule: str
    severity: str
    message: str
    reference: str = ""
    blocking: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "analyser": self.analyser,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "reference": self.reference,
            "blocking": self.blocking,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Finding":
        return Finding(
            file=data["file"],
            line=data["line"],
            analyser=data["analyser"],
            rule=data["rule"],
            severity=data["severity"],
            message=data["message"],
            reference=data.get("reference", ""),
            blocking=data.get("blocking", True),
        )


@dataclass(frozen=True)
class RuleResult:
    """The outcome half of an evidence record."""

    status: str
    subject: Subject
    violations: list[Violation] = field(default_factory=list)
    error: str = ""
    notes: tuple[str, ...] = ()
    supporting: tuple[Attestation, ...] = ()
    findings: tuple[Finding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "violations": [v.to_dict() for v in self.violations],
            "error": self.error or None,
            "notes": list(self.notes),
            "supporting": [a.to_dict() for a in self.supporting],
            "findings": [f.to_dict() for f in self.findings],
        }

    @staticmethod
    def from_dict(data: dict[str, Any], subject: Subject) -> "RuleResult":
        return RuleResult(
            status=data["status"],
            subject=subject,
            violations=[Violation.from_dict(v) for v in data.get("violations", [])],
            error=data.get("error") or "",
            notes=tuple(data.get("notes", [])),
            supporting=tuple(
                Attestation.from_dict(a) for a in data.get("supporting", [])
            ),
            findings=tuple(Finding.from_dict(f) for f in data.get("findings", [])),
        )
