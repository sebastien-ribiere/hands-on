"""SEC-001's engine: a real analyser, and the policy's threshold on top of it.

Two layers of test, on purpose. The parsing and threshold logic is tested
against canned bandit reports, so it is deterministic and runs anywhere. Then
one test runs bandit for real, because a parser that agrees with a fixture and
disagrees with the tool proves nothing at all -- it is skipped rather than
faked when bandit is not installed.
"""

import json
import subprocess
import sys
import textwrap

import pytest
from golden_thread_testkit import rule

from golden_thread.checks import security_scan
from golden_thread.results import ERROR, FAIL, PASS


def _bandit_works() -> bool:
    """Probe by running it, not by looking for a file with the right name.

    This machine has a `bandit` on PATH that is a broken shim: the file exists
    and importing it fails. `shutil.which` says yes and the tool says
    ModuleNotFoundError, which would make this test fail for a reason that has
    nothing to do with the code under test.
    """
    try:
        return subprocess.run(
            ["bandit", "--version"], capture_output=True, timeout=30
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


HAS_BANDIT = _bandit_works()


def canned(results, errors=()):
    """A python one-liner standing in for bandit, printing a fixed report."""
    report = json.dumps({"errors": list(errors), "results": results})
    exit_code = 1 if results else 0
    return [
        sys.executable,
        "-c",
        f"import sys; print({report!r}); sys.exit({exit_code})",
    ]


def finding(severity="MEDIUM", confidence="HIGH", test_id="B307", line=5):
    return {
        "filename": "src/spells/protection/ward.py",
        "line_number": line,
        "test_id": test_id,
        "issue_severity": severity,
        "issue_confidence": confidence,
        "issue_text": "Use of possibly insecure function.",
        "issue_cwe": {"id": 78, "link": "https://cwe.mitre.org/data/definitions/78.html"},
        "more_info": "https://bandit.readthedocs.io/b307",
    }


def a_rule(command=None, **overrides):
    params = {
        "format": "bandit",
        "command": command if command is not None else canned([]),
        "subject_root": "src",
        "subject_globs": ["**/*.py"],
        "fail_on_severity": "MEDIUM",
        "min_confidence": "MEDIUM",
    }
    params.update(overrides)
    return rule("SEC-001", security_scan.NAME, **params)


# --- the policy's threshold, over canned reports ------------------------


def test_a_clean_scan_passes(spellbook):
    result = security_scan.run(a_rule(), spellbook)
    assert result.status == PASS
    assert result.findings == ()


def test_a_finding_at_the_threshold_fails(spellbook):
    result = security_scan.run(a_rule(command=canned([finding()])), spellbook)
    assert result.status == FAIL
    assert [f.rule for f in result.findings] == ["B307"]
    assert result.findings[0].blocking is True


def test_a_finding_below_the_threshold_is_recorded_but_does_not_fail(spellbook):
    """A scanner whose output is filtered before anyone sees it is how a
    security requirement becomes decoration."""
    result = security_scan.run(
        a_rule(command=canned([finding(severity="LOW")])), spellbook
    )
    assert result.status == PASS
    assert len(result.findings) == 1
    assert result.findings[0].blocking is False
    assert any("below that threshold" in note for note in result.notes)


def test_a_low_confidence_finding_does_not_fail_this_profile(spellbook):
    result = security_scan.run(
        a_rule(command=canned([finding(confidence="LOW")])), spellbook
    )
    assert result.status == PASS
    assert result.findings[0].blocking is False


def test_the_threshold_is_policy_not_a_default(spellbook):
    """The same report, two profiles, two verdicts."""
    report = canned([finding(severity="LOW")])
    strict = security_scan.run(
        a_rule(command=report, fail_on_severity="LOW"), spellbook
    )
    lenient = security_scan.run(
        a_rule(command=report, fail_on_severity="HIGH"), spellbook
    )
    assert (strict.status, lenient.status) == (FAIL, PASS)


def test_the_analysers_own_words_are_kept(spellbook):
    result = security_scan.run(a_rule(command=canned([finding()])), spellbook)
    found = result.findings[0]
    assert found.analyser == "bandit"
    assert found.severity == "MEDIUM"
    assert found.message == "Use of possibly insecure function."
    assert found.reference == "https://bandit.readthedocs.io/b307"


def test_the_notes_say_which_threshold_was_applied(spellbook):
    result = security_scan.run(a_rule(), spellbook)
    assert any("fails on MEDIUM and above" in note for note in result.notes)


# --- everything that must not be reported as clean ----------------------


def test_a_scanner_that_crashed_is_error_not_pass(spellbook):
    """Exit 2 is how bandit says it failed, not that it found something."""
    result = security_scan.run(
        a_rule(
            command=[sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(2)"]
        ),
        spellbook,
    )
    assert result.status == ERROR
    assert "failed to run" in result.error


def test_unreadable_output_is_error_not_pass(spellbook):
    result = security_scan.run(
        a_rule(command=[sys.executable, "-c", "print('not json')"]), spellbook
    )
    assert result.status == ERROR
    assert "readable report" in result.error


def test_files_the_analyser_could_not_read_are_error_not_pass(spellbook):
    """PASS over files nothing looked at is a claim about unexamined code."""
    result = security_scan.run(
        a_rule(
            command=canned(
                [], errors=[{"filename": "src/x.py", "reason": "syntax error"}]
            )
        ),
        spellbook,
    )
    assert result.status == ERROR
    assert "could not scan every file" in result.error


def test_a_missing_analyser_is_error_not_pass(spellbook):
    result = security_scan.run(
        a_rule(command=["definitely-not-a-real-scanner-xyz"]), spellbook
    )
    assert result.status == ERROR


def test_an_empty_scan_is_not_a_pass(spellbook):
    result = security_scan.run(a_rule(subject_globs=["nowhere/*.py"]), spellbook)
    assert result.status == ERROR
    assert "scanned nothing" in result.error


def test_an_unknown_report_format_is_error_naming_what_is_supported(spellbook):
    result = security_scan.run(a_rule(format="sarif"), spellbook)
    assert result.status == ERROR
    assert "bandit" in result.error


def test_an_impossible_threshold_is_refused(spellbook):
    result = security_scan.run(a_rule(fail_on_severity="CATASTROPHIC"), spellbook)
    assert result.status == ERROR
    assert "LOW, MEDIUM, HIGH" in result.error


# --- and once, for real -------------------------------------------------


@pytest.mark.skipif(not HAS_BANDIT, reason="bandit is not installed here")
def test_bandit_really_finds_a_real_defect(spellbook):
    """The whole point of the engine, run against the actual tool."""
    real = a_rule(command=["bandit", "-r", "src", "-f", "json", "-q"])

    clean = security_scan.run(real, spellbook)
    assert clean.status == PASS, clean.error

    (spellbook / "src" / "spells" / "protection" / "ward.py").write_text(
        textwrap.dedent(
            '''
            """A ward that evaluates whatever it is handed."""


            def improvise(incantation: str) -> str:
                return str(eval(incantation))
            '''
        )
    )
    dirty = security_scan.run(real, spellbook)
    assert dirty.status == FAIL
    assert [f.rule for f in dirty.findings] == ["B307"]
    assert dirty.findings[0].file == "src/spells/protection/ward.py"
    assert dirty.findings[0].analyser == "bandit"
