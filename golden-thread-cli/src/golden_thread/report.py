"""The machine-readable report.

One JSON document per command, carrying the same evidence records the human
output describes. Nothing is summarised into a bare boolean: every claim in
here arrives with its subject, its producer and its method attached.
"""

import json
from typing import Any

from .manifest import Manifest
from .status import Status

REPORT_VERSION = 1


def build(command: str, status: Status) -> dict[str, Any]:
    manifest: Manifest = status.manifest
    return {
        "reportVersion": REPORT_VERSION,
        "command": command,
        "pathStatus": status.path_status,
        "exitCode": status.exit_code,
        "goldenThread": {
            "source": manifest.source,
            "ref": manifest.ref,
            "revision": manifest.revision,
            "profile": manifest.profile,
        },
        "requirements": [
            {
                "requirement": entry.requirement,
                "title": entry.title,
                "reportedStatus": entry.reported_status,
                "freshness": entry.freshness.to_dict(),
                "evidence": entry.evidence.to_dict() if entry.evidence else None,
            }
            for entry in status.entries
        ],
    }


def dumps(command: str, status: Status) -> str:
    return json.dumps(build(command, status), indent=2)


def json_dumps(document: dict[str, Any]) -> str:
    """The same JSON conventions, for the documents that are not a status."""
    return json.dumps(document, indent=2)
