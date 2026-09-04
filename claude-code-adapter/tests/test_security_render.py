"""A security finding is not import-graph shaped, and must not be shown as one.

The adapter renders `violations` as `source -> target`. A finding has neither.
Passing one through that path would print an arrow between two fields that do
not exist, which is a fabricated fact in a message a developer is meant to
trust. These tests pin the separate path, and the fact that findings the
profile set aside are not surfaced as problems.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

import render  # noqa: E402


def report(findings, path_status="OFF PATH"):
    return {
        "pathStatus": path_status,
        "goldenThread": {"ref": "v0.3.0", "profile": "academy-spells-done"},
        "requirements": [
            {
                "requirement": "SEC-001",
                "title": "No known security defect at MEDIUM or above",
                "reportedStatus": "FAIL",
                "freshness": {"state": "FRESH", "reasons": []},
                "evidence": {
                    "result": {
                        "status": "FAIL",
                        "violations": [],
                        "notes": ["ran `bandit -r src -f json -q` over 10 file(s)"],
                        "findings": findings,
                    }
                },
            }
        ],
    }


def finding(severity="MEDIUM", blocking=True, line=21, rule="B307"):
    return {
        "file": "src/spells/protection/ward.py",
        "line": line,
        "analyser": "bandit",
        "rule": rule,
        "severity": severity,
        "message": "Use of possibly insecure function.",
        "reference": "https://bandit.readthedocs.io/b307",
        "blocking": blocking,
    }


def test_a_finding_is_shown_with_its_location_and_the_analysers_rule_id():
    lines = render.deviation_lines(report([finding()]))
    assert any(
        "src/spells/protection/ward.py:21 MEDIUM B307 (bandit)" in line
        for line in lines
    )


def test_no_arrow_is_invented_for_a_finding():
    lines = render.deviation_lines(report([finding()]))
    assert not any("->" in line for line in lines)


def test_further_findings_are_counted_rather_than_listed():
    lines = render.deviation_lines(report([finding(), finding(line=30, rule="B102")]))
    assert any("(+1 more)" in line for line in lines)


def test_findings_below_the_profiles_threshold_are_not_reported_as_problems():
    """Repeating them as problems would misreport the policy the team is on."""
    lines = render.deviation_lines(
        report([finding(severity="LOW", blocking=False)])
    )
    # Falls back to the core's own notes rather than to a finding.
    assert not any("LOW" in line for line in lines)
    assert any("bandit" in line for line in lines)


def test_a_clean_path_says_nothing_at_all():
    assert render.deviation_lines(report([], path_status="ON PATH")) is None
