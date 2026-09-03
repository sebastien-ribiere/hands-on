#!/usr/bin/env python3
"""Claude Code PreToolUse hook: signal, never gate.

Fires before Edit/Write (see .claude/settings.json's matcher). Asks Golden
Thread's public CLI for the project's current status; if the path is not
clean, it hands Claude Code a message via `additionalContext` /
`systemMessage`. It never sets `permissionDecision` to anything but "allow",
and never exits non-zero for this reason -- there is no code path in this
file that can deny a tool call. Leaving the golden path stays possible; what
this hook guarantees is that the deviation is explicit, not silent.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from golden_thread_client import status  # noqa: E402
from render import deviation_lines  # noqa: E402


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    project_dir = payload.get("cwd", ".")

    report = status(project_dir)
    lines = deviation_lines(report)
    if lines is None:
        return 0  # nothing to say: no Golden Thread here, or the path is clean

    text = "\n".join(lines)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "additionalContext": text,
                },
                "systemMessage": text,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
