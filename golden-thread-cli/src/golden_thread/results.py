"""Verification results.

Deliberately concrete: a rule passed, failed, or could not run, and a failure
carries the exact locations that caused it. No generic evidence model.
"""

from dataclasses import dataclass, field
from typing import Any

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


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    title: str
    status: str
    violations: list[Violation] = field(default_factory=list)
    error: str = ""
    scanned_files: int = 0

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.rule_id,
            "title": self.title,
            "status": self.status,
            "scannedFiles": self.scanned_files,
            "violations": [v.to_dict() for v in self.violations],
        }
        if self.error:
            data["error"] = self.error
        return data


@dataclass(frozen=True)
class VerifyResult:
    profile: str
    ref: str
    revision: str
    timestamp: str
    rules: list[RuleResult]

    @property
    def status(self) -> str:
        # A rule that could not run is not a pass. Silence is never green.
        if any(r.status in (FAIL, ERROR) for r in self.rules):
            return FAIL
        if not self.rules:
            return ERROR
        return PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "ref": self.ref,
            "revision": self.revision,
            "timestamp": self.timestamp,
            "status": self.status,
            "rules": [r.to_dict() for r in self.rules],
        }
