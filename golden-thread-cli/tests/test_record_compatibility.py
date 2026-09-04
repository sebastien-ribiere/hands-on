"""Records written by earlier spikes must still load, unchanged.

Spike 5 added three fields: `findings` on a result, `blocking` on a finding,
and `command` on a method. Every one of them is additive with an empty default,
and this module is the thing that keeps that true -- the fixtures below are
literal Spike 2 and Spike 4 shapes, not records this code generated.

A record that fails to load is silently dropped by state.load, which means the
symptom of breaking this is not a crash. It is a project reporting INCOMPLETE
and quietly re-verifying, which is exactly the kind of quiet that this project
exists to remove.
"""

import json

from golden_thread.evidence import Evidence, Method
from golden_thread.results import Finding, RuleResult
from golden_thread.state import load, save
from golden_thread.subject import Subject

SPIKE_2_SUBJECT = {
    "kind": "worktree",
    "root": "src",
    "fileCount": 10,
    "digest": "sha256:" + "c" * 64,
    "gitRevision": "a" * 40,
    "gitDirty": False,
}

SPIKE_2_RECORD = {
    "evidenceVersion": 1,
    "requirement": "ARCH-001",
    "title": "Protection spells must not depend on Fire",
    "subject": SPIKE_2_SUBJECT,
    "producer": {"name": "golden-thread", "version": "0.2.0"},
    "method": {
        "check": "layered_dependencies",
        "profile": "academy-spells",
        "policyRef": "v0.1.0",
        "policyRevision": "b" * 40,
    },
    "result": {"status": "PASS", "violations": [], "error": None},
    "timestamp": "2026-08-28T07:53:51+00:00",
}

SPIKE_4_RECORD = {
    **SPIKE_2_RECORD,
    "requirement": "DOR-001",
    "method": {**SPIKE_2_RECORD["method"], "check": "spec_readiness"},
    "result": {
        "status": "FAIL",
        "violations": [],
        "error": None,
        "notes": ["assessed at 7/10, below the 8 this profile requires"],
        "supporting": [
            {
                "attestationVersion": 1,
                "requirement": "DOR-001",
                "kind": "assessment",
                "provider": "spec-readiness",
                "actor": "a model",
                "rubric": "spec-readiness@1.0.0",
                "subject": SPIKE_2_SUBJECT,
                "timestamp": "2026-09-03T10:00:00+00:00",
                "payload": {"score": 7},
            }
        ],
    },
}


def test_a_spike_2_record_still_loads():
    record = Evidence.from_dict(SPIKE_2_RECORD)
    assert record.requirement == "ARCH-001"
    assert record.result.status == "PASS"


def test_a_spike_2_method_has_no_command_rather_than_failing():
    record = Evidence.from_dict(SPIKE_2_RECORD)
    assert record.method.command == ()
    assert "[" not in str(record.method)


def test_a_spike_2_result_has_no_findings_rather_than_failing():
    assert Evidence.from_dict(SPIKE_2_RECORD).result.findings == ()


def test_a_spike_4_record_keeps_its_notes_and_supporting_claims():
    record = Evidence.from_dict(SPIKE_4_RECORD)
    assert record.result.notes == ("assessed at 7/10, below the 8 this profile requires",)
    assert record.result.supporting[0].actor == "a model"
    assert record.result.findings == ()


def test_old_records_survive_a_round_trip_through_the_store(tmp_path):
    """The failure mode is silence: an unreadable record is dropped, and the
    project reports INCOMPLETE rather than raising."""
    project = tmp_path / "project"
    project.mkdir()
    (project / ".golden-thread").mkdir()
    (project / ".golden-thread" / "evidence.json").write_text(
        json.dumps({"evidenceVersion": 1, "evidence": [SPIKE_2_RECORD, SPIKE_4_RECORD]})
    )

    loaded = load(project)
    assert sorted(loaded) == ["ARCH-001", "DOR-001"]

    save(project, list(loaded.values()))
    assert sorted(load(project)) == ["ARCH-001", "DOR-001"]


def test_a_finding_without_blocking_is_read_as_blocking():
    """The conservative reading: a recorded finding whose file predates the
    field was one the profile failed on."""
    finding = Finding.from_dict(
        {
            "file": "src/x.py",
            "line": 5,
            "analyser": "bandit",
            "rule": "B307",
            "severity": "MEDIUM",
            "message": "eval",
        }
    )
    assert finding.blocking is True
    assert finding.reference == ""


def test_a_new_record_round_trips_with_everything_on_it():
    subject = Subject.from_dict(SPIKE_2_SUBJECT)
    original = RuleResult(
        status="FAIL",
        subject=subject,
        notes=("ran `bandit`",),
        findings=(
            Finding("src/x.py", 5, "bandit", "B307", "MEDIUM", "eval", "http://x", True),
            Finding("src/y.py", 9, "bandit", "B101", "LOW", "assert", "", False),
        ),
    )
    restored = RuleResult.from_dict(original.to_dict(), subject)
    assert restored == original


def test_a_method_with_a_command_round_trips():
    method = Method(
        check="external_command",
        profile="academy-spells-done",
        policy_ref="v0.3.0",
        policy_revision="d" * 40,
        command=("python3", "-m", "pytest", "-q", "tests"),
    )
    assert Method.from_dict(method.to_dict()) == method
    assert "[python3 -m pytest -q tests]" in str(method)
