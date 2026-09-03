from conftest import break_arch_001, verify


def test_silent_when_project_is_not_attached(run_hook, project):
    assert run_hook("session_start.py", project) is None


def test_shows_context_before_any_verify(run_hook, attached):
    output = run_hook("session_start.py", attached)
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    ctx = output["hookSpecificOutput"]["additionalContext"]
    assert "Golden Thread v0.1.0" in ctx
    assert "Profile: academy-spells" in ctx
    assert "Status: INCOMPLETE" in ctx
    assert output["systemMessage"] == ctx


def test_shows_on_path_after_verify(run_hook, attached):
    verify(attached)
    ctx = run_hook("session_start.py", attached)["hookSpecificOutput"]["additionalContext"]
    assert "Status: ON PATH" in ctx
    assert "ARCH-001" not in ctx  # a clean path carries no per-requirement noise


def test_shows_off_path_and_the_real_violation(run_hook, attached):
    break_arch_001(attached)
    verify(attached)
    ctx = run_hook("session_start.py", attached)["hookSpecificOutput"]["additionalContext"]
    assert "Status: OFF PATH" in ctx
    assert "ARCH-001" in ctx
    assert "spells.elements.fire" in ctx
