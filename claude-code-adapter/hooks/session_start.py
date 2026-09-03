#!/usr/bin/env python3
"""Claude Code SessionStart hook: surface the Golden Thread context.

Reads the hook's stdin JSON (Claude Code's own schema), asks Golden Thread's
public CLI for the project's current status, and if there is one, hands it
back to Claude Code as `hookSpecificOutput.additionalContext` -- the
documented mechanism for injecting context at session start.

Silent (exit 0, no output) when the project is not attached to a Golden
Thread: most projects on a machine won't be, and that must not be noise.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from golden_thread_client import status  # noqa: E402
from render import context_lines  # noqa: E402


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    project_dir = payload.get("cwd", ".")

    report = status(project_dir)
    if report is None:
        return 0

    text = "\n".join(context_lines(report))
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": text,
                },
                "systemMessage": text,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
