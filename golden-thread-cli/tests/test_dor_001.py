"""DOR-001: a requirement Golden Thread cannot satisfy on its own.

The claims these tests are pinning, in order of how much they matter:

  1. an acceptable score never satisfies the requirement alone -- not at the
     threshold, not at full marks;
  2. a human approval never satisfies it alone either: the threshold is
     policy, and signing does not move it;
  3. both claims are tied to the exact text they were made about, and to the
     exact rubric version they were made under;
  4. none of this is a gate. NOT READY is reported, never enforced.
"""

import json

import pytest

from golden_thread import state, status as status_mod
from golden_thread.attestation import ASSESSMENT, HUMAN_ATTESTATION
from golden_thread.results import FAIL, PASS
from golden_thread_testkit import assessment, publish_dor


def attach(cli, spellbook, source, ref="v0.2.0"):
    assert cli(["-C", str(spellbook), "init", "--source", str(source),
                "--ref", ref, "--profile", "academy-spells-ready"]) == 0


def assess(cli, spellbook, tmp_path, data):
    path = tmp_path / "assessment.json"
    path.write_text(json.dumps(data))
    return cli(["-C", str(spellbook), "readiness", "assess", "--input", str(path)])


def approve(cli, spellbook, phrase=None, **flags):
    args = ["-C", str(spellbook), "readiness", "approve",
            "--attestor", "someone@example.invalid"]
    for key, value in flags.items():
        args += [f"--{key}", value] if value is not True else [f"--{key}"]
    if phrase is not None:
        args += ["--confirm", phrase]
    return cli(args)


def challenge(spellbook):
    from golden_thread import manifest as manifest_mod, readiness

    target = readiness.resolve(spellbook, manifest_mod.read(spellbook))
    return readiness.challenge(target)


def entry_for(spellbook, requirement="DOR-001"):
    from golden_thread import manifest as manifest_mod

    result = status_mod.compute(spellbook, manifest_mod.read(spellbook))
    return result, next(e for e in result.entries if e.requirement == requirement)


# --- the two halves, and why neither is enough -------------------------


def test_nothing_recorded_is_not_ready(cli, dor_source, spellbook, mission, capsys):
    attach(cli, spellbook, dor_source)
    assert cli(["-C", str(spellbook), "verify"]) == 4

    out = capsys.readouterr().out
    assert "NOT READY" in out
    assert "no readiness assessment on record" in out
    assert "no human approval on record" in out


def test_a_score_at_the_threshold_does_not_satisfy_the_requirement(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    """The headline claim: 8/10 is eligibility for a decision, not a decision."""
    attach(cli, spellbook, dor_source)
    assert assess(cli, spellbook, tmp_path, assessment(score=8)) == 0

    assert cli(["-C", str(spellbook), "verify"]) == 4
    out = capsys.readouterr().out
    assert "no human approval on record" in out
    _, entry = entry_for(spellbook)
    assert entry.evidence.result.status == FAIL


def test_a_perfect_score_does_not_satisfy_the_requirement_either(
    cli, dor_source, spellbook, mission, tmp_path
):
    """10/10 changes nothing. There is no score that approves itself."""
    attach(cli, spellbook, dor_source)
    assess(cli, spellbook, tmp_path, assessment(score=10))

    assert cli(["-C", str(spellbook), "verify"]) == 4
    _, entry = entry_for(spellbook)
    assert entry.evidence.result.status == FAIL


def test_a_human_approval_does_not_move_the_threshold(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    """The symmetric claim: the score is policy, and signing does not edit it."""
    attach(cli, spellbook, dor_source)
    assess(cli, spellbook, tmp_path, assessment(score=7))
    assert approve(cli, spellbook, challenge(spellbook)) == 0

    assert cli(["-C", str(spellbook), "verify"]) == 4
    out = capsys.readouterr().out
    assert "below the 8 this profile requires" in out


def test_both_halves_together_satisfy_it(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    attach(cli, spellbook, dor_source)
    assess(cli, spellbook, tmp_path, assessment(score=9))
    approve(cli, spellbook, challenge(spellbook))
    capsys.readouterr()

    assert cli(["-C", str(spellbook), "verify"]) == 0
    out = capsys.readouterr().out
    assert "PATH STATUS   ON PATH" in out
    # A verdict is never bare: both claims it rests on are named.
    assert "rests on  assessment" in out
    assert "rests on  human-attestation" in out
    assert "neither would have been enough alone" in out


def test_a_blocker_beats_any_score(cli, dor_source, spellbook, mission, tmp_path, capsys):
    attach(cli, spellbook, dor_source)
    assess(cli, spellbook, tmp_path,
           assessment(score=10, blockers=["the upstream API does not exist yet"]))
    approve(cli, spellbook, challenge(spellbook))

    assert cli(["-C", str(spellbook), "verify"]) == 4
    assert "1 blocker(s)" in capsys.readouterr().out


def test_a_refusal_is_recorded_with_its_reason(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    attach(cli, spellbook, dor_source)
    assess(cli, spellbook, tmp_path, assessment(score=10))
    assert approve(cli, spellbook, challenge(spellbook), reject=True,
                   note="the frost taxonomy is being rewritten this month") == 0

    assert cli(["-C", str(spellbook), "verify"]) == 4
    out = capsys.readouterr().out
    assert "rejected" in out
    assert "frost taxonomy" in out


# --- what the claims are tied to ---------------------------------------


def test_neither_claim_survives_an_edit_to_the_mission(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    """An approval is given to a text, not to a file name."""
    attach(cli, spellbook, dor_source)
    assess(cli, spellbook, tmp_path, assessment(score=9))
    approve(cli, spellbook, challenge(spellbook))
    assert cli(["-C", str(spellbook), "verify"]) == 0

    mission.write_text("# Mission: frost ward\n\nActually, build a fire lance.\n")
    capsys.readouterr()

    assert cli(["-C", str(spellbook), "verify"]) == 4
    out = capsys.readouterr().out
    assert "the assessment was made about a different version of the mission" in out
    assert "the human-attestation was made about a different version" in out


def test_an_assessment_does_not_survive_a_rubric_version_change(
    cli, corporate_source, spellbook, mission, tmp_path, capsys
):
    """This is what versioning the rubric buys.

    A score produced under 1.0.0 is not silently reinterpreted as a score
    under 1.1.0. The recorded assessment names the rubric it was made under,
    and stops applying when the profile pins a different one.
    """
    publish_dor(corporate_source, tag="v0.2.0", rubric_version="1.0.0")
    attach(cli, spellbook, corporate_source, ref="v0.2.0")
    assess(cli, spellbook, tmp_path, assessment(score=9))
    approve(cli, spellbook, challenge(spellbook))
    assert cli(["-C", str(spellbook), "verify"]) == 0

    # The Academy publishes a revised rubric and the project moves onto it.
    publish_dor(corporate_source, tag="v0.3.0", rubric_version="1.1.0")
    attach(cli, spellbook, corporate_source, ref="v0.3.0")
    capsys.readouterr()

    assert cli(["-C", str(spellbook), "verify"]) == 4
    out = capsys.readouterr().out
    assert "spec-readiness@1.0.0" in out
    assert "spec-readiness@1.1.0" in out


def test_a_missing_mission_is_reported_not_assumed(
    cli, dor_source, spellbook, capsys
):
    """No mission file at all is a fact about the subject, not a pass."""
    attach(cli, spellbook, dor_source)
    assert cli(["-C", str(spellbook), "verify"]) == 4
    assert "no mission document found" in capsys.readouterr().out


# --- precedence and reporting ------------------------------------------


def test_not_ready_outranks_off_path(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    """Both requirements fail. The headline is the one that comes first in time."""
    attach(cli, spellbook, dor_source)
    ward = spellbook / "src" / "spells" / "protection" / "ward.py"
    ward.write_text(
        "from ..elements import fire\n\n\ndef cast():\n    return fire.scorch('x')\n"
    )

    assert cli(["-C", str(spellbook), "verify"]) == 4
    out = capsys.readouterr().out
    assert "PATH STATUS   NOT READY" in out
    # Nothing is hidden: the architecture failure is still reported in full.
    assert "FAIL   ARCH-001" in out


def test_the_signal_never_becomes_a_gate(cli, dor_source, spellbook, mission):
    """NOT READY is a report. Nothing in the core refuses to do anything."""
    attach(cli, spellbook, dor_source)
    cli(["-C", str(spellbook), "verify"])

    # The developer writes the code anyway, and the tool keeps working.
    (spellbook / "src" / "spells" / "protection" / "frost_ward.py").write_text(
        "from ..elements import water\n\n\ndef cast(t):\n    return water.mist()\n"
    )
    assert cli(["-C", str(spellbook), "verify"]) == 4


def test_the_json_report_carries_the_supporting_claims(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    """What the adapter reads. Both claims travel with the verdict."""
    attach(cli, spellbook, dor_source)
    assess(cli, spellbook, tmp_path, assessment(score=9))
    approve(cli, spellbook, challenge(spellbook))
    cli(["-C", str(spellbook), "verify"])
    capsys.readouterr()

    cli(["-C", str(spellbook), "status", "--json"])
    report = json.loads(capsys.readouterr().out)

    assert report["pathStatus"] == "ON PATH"
    dor = next(r for r in report["requirements"] if r["requirement"] == "DOR-001")
    assert dor["reportedStatus"] == PASS
    kinds = {c["kind"] for c in dor["evidence"]["result"]["supporting"]}
    assert kinds == {ASSESSMENT, HUMAN_ATTESTATION}
    scoring = next(
        c for c in dor["evidence"]["result"]["supporting"] if c["kind"] == ASSESSMENT
    )
    assert scoring["rubric"] == "spec-readiness@1.0.0"
    assert scoring["payload"]["score"] == 9
    assert dor["evidence"]["result"]["notes"]


def test_not_ready_exit_code_is_its_own(cli, dor_source, spellbook, mission, tmp_path):
    """4 is distinguishable from 1: not agreed is not the same as broken."""
    attach(cli, spellbook, dor_source)
    assert cli(["-C", str(spellbook), "verify"]) == 4
    assert status_mod.EXIT_CODES[status_mod.NOT_READY] == 4
    assert status_mod.EXIT_CODES[status_mod.OFF_PATH] == 1


def test_the_two_stores_stay_separate(
    cli, dor_source, spellbook, mission, tmp_path
):
    """What this tool proved and what it was told are kept apart on disk."""
    attach(cli, spellbook, dor_source)
    assess(cli, spellbook, tmp_path, assessment(score=9))
    approve(cli, spellbook, challenge(spellbook))
    cli(["-C", str(spellbook), "verify"])

    claims = state.load_attestations(spellbook, "DOR-001")
    assert {c.kind for c in claims} == {ASSESSMENT, HUMAN_ATTESTATION}
    assert all(c.provider in ("spec-readiness", "human") for c in claims)

    evidence = state.load(spellbook)
    assert set(evidence) == {"DOR-001", "ARCH-001"}
    assert evidence["DOR-001"].producer.name == "golden-thread"
