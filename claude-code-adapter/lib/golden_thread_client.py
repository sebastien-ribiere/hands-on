"""The only place this adapter touches Golden Thread.

It shells out to the `golden-thread` command exactly as any other consumer
would: the public CLI contract (`status --json`), nothing else. No import of
`golden_thread` internals, no private state file reached into directly. If the
core ever changes its internals, this still works; if the core ever drops
Claude Code support, it loses nothing, because it never had any.

Deliberately narrow: only `status`. This adapter never calls `verify` -- it
never runs a check on the developer's behalf. Verification stays a deliberate
developer action; the adapter only ever reads what was last recorded and
whether that record still applies.

The executable is `$GOLDEN_THREAD_BIN` if set, else the bare command
`golden-thread` on PATH. The override exists because a bare command name is
not guaranteed to be *this* tool -- on the machine this was built on, an
unrelated, already-installed package happens to occupy that same name (see
the adapter README). A real install would not have that collision; this
still fails safely if it does, see below.
"""

import json
import os
import subprocess
from typing import Any

NOT_ATTACHED = 2  # golden-thread's own exit code for "no manifest here"
BIN = os.environ.get("GOLDEN_THREAD_BIN", "golden-thread")


def status(project_dir: str) -> dict[str, Any] | None:
    """Run `golden-thread -C project_dir status --json`.

    Returns None when there is nothing to report: golden-thread is not
    installed, or this project was never attached to a Golden Thread. Neither
    is a deviation -- most directories on a machine won't be Golden Thread
    projects, and that must stay silent.
    """
    try:
        proc = subprocess.run(
            [BIN, "-C", project_dir, "status", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if proc.returncode == NOT_ATTACHED:
        return None

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
