"""What a check engine returns.

Deliberately concrete: a rule passed, failed, or could not run, a failure
carries the exact locations that caused it, and the result carries the subject
it was produced from. No generic evidence taxonomy.
"""

from dataclasses import dataclass, field
from typing import Any

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
class RuleResult:
    """The outcome half of an evidence record."""

    status: str
    subject: Subject
    violations: list[Violation] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "violations": [v.to_dict() for v in self.violations],
            "error": self.error or None,
        }

    @staticmethod
    def from_dict(data: dict[str, Any], subject: Subject) -> "RuleResult":
        return RuleResult(
            status=data["status"],
            subject=subject,
            violations=[Violation.from_dict(v) for v in data.get("violations", [])],
            error=data.get("error") or "",
        )
