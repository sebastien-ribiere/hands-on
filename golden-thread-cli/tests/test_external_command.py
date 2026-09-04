"""TEST-001's engine: a command the policy names, and its exit code."""

import sys

import pytest
from golden_thread_testkit import rule

from golden_thread.checks import external_command
from golden_thread.results import ERROR, FAIL, PASS


def a_rule(**overrides):
    params = {
        "command": [sys.executable, "-c", "import sys; sys.exit(0)"],
        "subject_globs": ["src/**/*.py"],
    }
    params.update(overrides)
    return rule("TEST-001", external_command.NAME, **params)


def test_exit_zero_is_the_verdict(spellbook):
    result = external_command.run(a_rule(), spellbook)
    assert result.status == PASS


def test_a_failing_command_fails_the_requirement(spellbook):
    result = external_command.run(
        a_rule(command=[sys.executable, "-c", "import sys; sys.exit(3)"]), spellbook
    )
    assert result.status == FAIL
    assert "exit 3" in result.notes[0]


def test_the_command_that_ran_is_in_the_result_for_a_pass_too(spellbook):
    """A verdict is never shown without the reason it is that verdict."""
    result = external_command.run(a_rule(), spellbook)
    assert any("ran `" in note for note in result.notes)


def test_what_a_failing_command_said_is_kept(spellbook):
    result = external_command.run(
        a_rule(
            command=[
                sys.executable,
                "-c",
                "import sys; print('4 failed, 6 passed'); sys.exit(1)",
            ]
        ),
        spellbook,
    )
    assert result.status == FAIL
    assert any("4 failed, 6 passed" in note for note in result.notes)


def test_a_missing_binary_is_error_not_failure(spellbook):
    """"We did not check" and "it failed" are different facts."""
    result = external_command.run(
        a_rule(command=["definitely-not-a-real-binary-xyz"]), spellbook
    )
    assert result.status == ERROR
    assert "not available" in result.error


def test_a_timeout_is_error_not_failure(spellbook):
    result = external_command.run(
        a_rule(
            command=[sys.executable, "-c", "import time; time.sleep(30)"],
            timeout_seconds=1,
        ),
        spellbook,
    )
    assert result.status == ERROR
    assert "did not finish" in result.error


def test_an_exit_zero_over_no_files_is_not_a_pass(spellbook):
    """A command that ran against nothing has established nothing."""
    result = external_command.run(a_rule(subject_globs=["nowhere/**/*.py"]), spellbook)
    assert result.status == ERROR
    assert "ran against nothing" in result.error


def test_a_command_declared_as_a_string_is_refused(spellbook):
    """No shell is used, so a string cannot be interpreted -- and quietly
    splitting it on spaces is how `rm -rf $EMPTY` gets executed."""
    result = external_command.run(a_rule(command="pytest -q tests"), spellbook)
    assert result.status == ERROR
    assert "list of arguments" in result.error


def test_a_rule_with_no_subject_globs_is_refused(spellbook):
    result = external_command.run(
        rule("TEST-001", external_command.NAME, command=["true"]), spellbook
    )
    assert result.status == ERROR
    assert "subject_globs" in result.error


def test_the_subject_moves_when_a_declared_file_changes(spellbook):
    before = external_command.subject(a_rule(), spellbook)
    (spellbook / "src" / "spells" / "elements" / "air.py").write_text("x = 1\n")
    after = external_command.subject(a_rule(), spellbook)
    assert before.digest != after.digest


def test_the_subject_ignores_what_the_globs_never_named(spellbook):
    """False invalidation is how a staleness mechanism gets ignored."""
    before = external_command.subject(a_rule(), spellbook)
    (spellbook / "NOTES.md").write_text("prose, not code\n")
    assert external_command.subject(a_rule(), spellbook).digest == before.digest


@pytest.mark.parametrize("globs", [["src/**/*.py", "tests/**/*.py"]])
def test_the_subject_spans_every_declared_glob(spellbook, globs):
    (spellbook / "tests").mkdir()
    before = external_command.subject(a_rule(subject_globs=globs), spellbook)
    (spellbook / "tests" / "test_x.py").write_text("def test_x():\n    pass\n")
    after = external_command.subject(a_rule(subject_globs=globs), spellbook)
    assert after.file_count == before.file_count + 1
