from conftest import break_arch_001, verify


def test_allows_and_silent_when_not_attached(run_hook, project):
    assert run_hook("pre_tool_use.py", project) is None


def test_allows_and_silent_when_on_path(run_hook, attached):
    verify(attached)
    assert run_hook("pre_tool_use.py", attached) is None


def test_signals_without_denying_before_first_verify(run_hook, attached):
    output = run_hook("pre_tool_use.py", attached)
    hso = output["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "GOLDEN THREAD DEVIATION" in hso["additionalContext"]
    assert "never verified" in hso["additionalContext"]


def test_signals_without_denying_when_off_path(run_hook, attached):
    break_arch_001(attached)
    verify(attached)
    output = run_hook("pre_tool_use.py", attached)
    hso = output["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "GOLDEN THREAD DEVIATION" in hso["additionalContext"]
    assert "Missing: ARCH-001" in hso["additionalContext"]
    assert "spells.elements.fire" in hso["additionalContext"]


def test_signals_without_denying_when_stale(run_hook, attached):
    verify(attached)
    # the code changes again without re-verifying
    shield = attached / "src" / "spells" / "protection" / "shield.py"
    shield.write_text(shield.read_text() + "\n# a later thought\n")

    output = run_hook("pre_tool_use.py", attached)
    hso = output["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "evidence is stale" in hso["additionalContext"]
