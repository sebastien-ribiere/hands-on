"""Where recorded evidence lives.

`status` reports evidence, it does not produce it. That keeps the two commands
honest about which one actually ran the rules.

Records are keyed by requirement and the file holds the *latest* record for
each: this is a current-state file, not an audit journal.

Attestations -- claims Golden Thread received rather than produced -- live in
their own file, under the same rule: latest wins, keyed by requirement *and*
kind, so a fresh assessment replaces the previous assessment without touching
the human approval, and vice versa. Two files rather than one because the
distinction between what this tool proved and what it was told is the whole
point of keeping them.
"""

import json
from pathlib import Path

from .attestation import ATTESTATION_VERSION, Attestation
from .evidence import EVIDENCE_VERSION, Evidence
from .paths import attestations_path, evidence_path, work_dir


def save(project: Path, records: list[Evidence]) -> Path:
    """Merge records in by requirement, leaving untouched requirements alone."""
    merged = load(project)
    for record in records:
        merged[record.requirement] = record

    work_dir(project).mkdir(parents=True, exist_ok=True)
    path = evidence_path(project)
    path.write_text(
        json.dumps(
            {
                "evidenceVersion": EVIDENCE_VERSION,
                "evidence": [merged[k].to_dict() for k in sorted(merged)],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def load(project: Path) -> dict[str, Evidence]:
    path = evidence_path(project)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    records = {}
    for raw in data.get("evidence", []):
        try:
            record = Evidence.from_dict(raw)
        except (KeyError, TypeError):
            continue  # an unreadable record is no record, never a verdict
        records[record.requirement] = record
    return records


def save_attestation(project: Path, attestation: Attestation) -> Path:
    """Record a received claim, replacing the last one of the same kind."""
    merged = {(a.requirement, a.kind): a for a in load_attestations(project)}
    merged[(attestation.requirement, attestation.kind)] = attestation

    work_dir(project).mkdir(parents=True, exist_ok=True)
    path = attestations_path(project)
    path.write_text(
        json.dumps(
            {
                "attestationVersion": ATTESTATION_VERSION,
                "attestations": [merged[k].to_dict() for k in sorted(merged)],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def load_attestations(project: Path, requirement: str | None = None) -> list[Attestation]:
    path = attestations_path(project)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    records = []
    for raw in data.get("attestations", []):
        try:
            record = Attestation.from_dict(raw)
        except (KeyError, TypeError):
            continue  # an unreadable claim is no claim
        if requirement is None or record.requirement == requirement:
            records.append(record)
    return records


def latest_attestation(
    project: Path, requirement: str, kind: str
) -> Attestation | None:
    for record in load_attestations(project, requirement):
        if record.kind == kind:
            return record
    return None
