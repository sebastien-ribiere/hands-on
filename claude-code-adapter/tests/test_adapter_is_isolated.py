"""The adapter's own structural guards.

Mirrors golden-thread-cli/tests/test_core_is_harness_agnostic.py from the
other side: that test proves the core cannot see Claude Code. These prove the
Claude Code adapter (a) never reaches into the core's internals -- it only
ever calls the public `golden-thread` command -- and (b) can never deny or
block a tool call: "not a prison" is enforced by construction, not by review.
"""

import re
from pathlib import Path

ADAPTER = Path(__file__).resolve().parents[1]
PYTHON_FILES = [*ADAPTER.glob("hooks/*.py"), *ADAPTER.glob("lib/*.py")]

FORBIDDEN_IMPORT = re.compile(r"^\s*(import|from)\s+golden_thread\b", re.MULTILINE)
FORBIDDEN_DECISION = re.compile(r'"deny"|"ask"')


def test_never_imports_core_internals():
    offenders = [
        p.relative_to(ADAPTER) for p in PYTHON_FILES if FORBIDDEN_IMPORT.search(p.read_text())
    ]
    assert offenders == [], (
        f"adapter reaches into golden_thread internals: {offenders} "
        "-- it must only call the public `golden-thread` command"
    )


def test_only_talks_to_the_core_through_the_subprocess_call():
    client = (ADAPTER / "lib" / "golden_thread_client.py").read_text()
    assert '"golden-thread"' in client
    assert "subprocess" in client


def test_no_hook_can_deny_or_ask_permission():
    for path in ADAPTER.glob("hooks/*.py"):
        offenders = FORBIDDEN_DECISION.findall(path.read_text())
        assert offenders == [], f"{path.name} can set a permissionDecision of {offenders}"


def test_no_hook_ever_returns_a_non_zero_exit_code():
    """The only way this adapter could gate is a non-zero exit. It never does."""
    for path in ADAPTER.glob("hooks/*.py"):
        text = path.read_text()
        assert re.search(r"return\s+[1-9]\d*\b", text) is None, (
            f"{path.name} has a code path that could exit non-zero"
        )
