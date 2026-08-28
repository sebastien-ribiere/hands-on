"""Path status: what the project's evidence says about the code in front of us.

  INCOMPLETE  nothing has been verified yet
  ON PATH     every requirement has current, passing evidence
  OFF PATH    a requirement failed, on evidence that still applies
  STALE       evidence exists but no longer describes this code or this policy

Order of precedence, most definite fact first: a confirmed failure is a fact
and outranks staleness; unknown outranks a comfortable assumption. ON PATH is
only claimed when every requirement is both current and passing.

OFF PATH is a signal, not a gate. Golden Thread reports a deviation; it does
not prevent one.
"""

from dataclasses import dataclass
from pathlib import Path

from . import checks, evidence as evidence_mod, policy, source, state
from .evidence import FRESH, NEVER, Evidence, Freshness
from .manifest import Manifest
from .results import ERROR, FAIL, UNKNOWN

INCOMPLETE = "INCOMPLETE"
ON_PATH = "ON PATH"
OFF_PATH = "OFF PATH"
STALE = "STALE"

EXIT_CODES = {ON_PATH: 0, INCOMPLETE: 0, OFF_PATH: 1, STALE: 3}


@dataclass(frozen=True)
class Entry:
    """One requirement, its evidence, and whether that evidence still applies."""

    requirement: str
    title: str
    evidence: Evidence | None
    freshness: Freshness

    @property
    def reported_status(self) -> str:
        """Never report a recorded verdict that no longer applies."""
        if self.evidence is None:
            return UNKNOWN
        if not self.freshness.is_fresh:
            return STALE
        return self.evidence.result.status


@dataclass(frozen=True)
class Status:
    manifest: Manifest
    entries: list[Entry]
    path_status: str

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.path_status]


def _aggregate(entries: list[Entry]) -> str:
    if not entries or all(e.evidence is None for e in entries):
        return INCOMPLETE
    if any(
        e.freshness.is_fresh and e.evidence.result.status in (FAIL, ERROR)
        for e in entries
        if e.evidence is not None
    ):
        return OFF_PATH
    if any(not e.freshness.is_fresh for e in entries):
        return STALE
    return ON_PATH


def compute(project: Path, manifest: Manifest) -> Status:
    """Read evidence and re-identify each subject. Runs no check.

    Re-identifying a subject is not producing evidence: nothing is verified
    here, we only establish whether what was recorded still applies.
    """
    source_root = source.ensure_available(project, manifest)
    profile = policy.load_profile(source_root, manifest.profile)
    recorded = state.load(project)

    entries: list[Entry] = []
    for rule in profile.rules:
        engine = checks.get(rule.check)
        current = engine.subject(rule, project)
        record = recorded.get(rule.id)
        if record is None:
            freshness = Freshness(
                state=NEVER, reasons=("never verified",), current_subject=current
            )
        else:
            freshness = evidence_mod.assess(record, current, manifest)
        entries.append(
            Entry(
                requirement=rule.id,
                title=rule.title,
                evidence=record,
                freshness=freshness,
            )
        )

    return Status(manifest=manifest, entries=entries, path_status=_aggregate(entries))


def from_records(manifest: Manifest, records: list[Evidence]) -> Status:
    """The status implied by records just produced, which are fresh by fiat."""
    entries = [
        Entry(
            requirement=record.requirement,
            title=record.title,
            evidence=record,
            freshness=Freshness(
                state=FRESH, reasons=(), current_subject=record.subject
            ),
        )
        for record in records
    ]
    return Status(manifest=manifest, entries=entries, path_status=_aggregate(entries))
