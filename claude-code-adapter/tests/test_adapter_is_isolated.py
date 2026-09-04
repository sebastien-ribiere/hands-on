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


# --- the skill may assess, and may never approve -----------------------

SKILLS = ADAPTER / "skills"
FENCE = re.compile(r"```(?:bash|sh|shell)\n(.*?)```", re.DOTALL)


def _runnable_commands(text: str) -> str:
    """Only what the skill actually tells an agent to run.

    Greping the whole file would be useless here: the skill's prohibition
    against approving necessarily contains the word "approve". What must not
    exist is an *executable* instruction to approve, so this looks only inside
    the shell fences.
    """
    return "\n".join(FENCE.findall(text))


def test_the_skill_never_instructs_an_agent_to_approve():
    """A readiness score is an assessment; approval is a decision by a person.

    The skill produces the first and must never produce the second. This is
    the same kind of guard as the ones above: not a convention to be
    remembered in review, but a test that fails the moment a command that
    records an approval appears among the ones the skill runs.
    """
    for path in SKILLS.glob("*/SKILL.md"):
        commands = _runnable_commands(path.read_text())
        assert "approve" not in commands, (
            f"{path.parent.name} tells an agent to run an approval: "
            "recording a human decision is not the agent's to run"
        )
        assert "--confirm" not in commands, (
            f"{path.parent.name} tells an agent to supply an approval "
            "confirmation phrase"
        )


def test_no_skill_instructs_an_agent_to_attest():
    """The same guard, for the requirement nothing can check.

    An agent that could record the cookie attestation would be claiming that a
    person did something in the physical world. It is a stronger version of the
    approval case: there, a model at least read the assessment it was signing
    off. Here there is nothing to read.
    """
    for path in SKILLS.glob("*/SKILL.md"):
        commands = _runnable_commands(path.read_text())
        assert "golden-thread attest" not in commands, (
            f"{path.parent.name} tells an agent to record an attestation: "
            "a claim about what a person did is not the agent's to make"
        )


def test_no_skill_stamps_documentation_on_a_developers_behalf():
    """Cheap is not the same as automatic.

    `docs stamp` is deliberately one command, because a gate expensive enough
    to resent gets routed around. That reasoning only holds while a person runs
    it: a skill that stamped after editing code would turn the claim "somebody
    re-stamped this against this code" into "the tool did", which is a claim
    about nothing.
    """
    for path in SKILLS.glob("*/SKILL.md"):
        commands = _runnable_commands(path.read_text())
        assert "golden-thread docs stamp" not in commands, (
            f"{path.parent.name} tells an agent to stamp the documentation"
        )


def test_the_skill_says_so_in_words_as_well():
    """The structural guard above stops the command. This stops the intent."""
    skill = (SKILLS / "spec-readiness" / "SKILL.md").read_text()
    assert "Never run `golden-thread readiness approve`" in skill
    assert "10/10" in skill, "the skill must address the perfect-score case"


def test_the_skill_reads_the_rubric_from_the_project_rather_than_from_memory():
    """A rubric remembered from another project is not this project's policy."""
    commands = _runnable_commands(
        (SKILLS / "spec-readiness" / "SKILL.md").read_text()
    )
    assert "golden-thread readiness rubric --json" in commands
    assert "golden-thread readiness assess" in commands
