"""Where recorded evidence lives.

`status` reports evidence, it does not produce it. That keeps the two commands
honest about which one actually ran the rules.

Records are keyed by requirement and the file holds the *latest* record for
each: this is a current-state file, not an audit journal.
"""

import json
from pathlib import Path

from .evidence import EVIDENCE_VERSION, Evidence
from .paths import evidence_path, work_dir


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
