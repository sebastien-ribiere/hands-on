"""The readiness commands: what they publish, what they refuse, what they record.

Two things are being pinned here.

The first is that `readiness assess` performs a *real* structural check on a
submitted assessment rather than accepting whatever arrives. The rubric says
what the dimensions are and what each is worth; an assessment that does not
match it, or whose headline score is not the sum of its parts, is refused. A
number nobody can argue with underneath is not an assessment.

The second is the approval boundary, and what it does and does not claim. It
makes approval a deliberate act tied to a specific text. It does not
authenticate anybody, and no test here pretends otherwise.
"""

import json

import pytest

from golden_thread import readiness, state
from golden_thread.attestation import HUMAN_ATTESTATION
from golden_thread_testkit import assessment


def attach(cli, spellbook, source):
    assert cli(["-C", str(spellbook), "init", "--source", str(source),
                "--ref", "v0.2.0", "--profile", "academy-spells-ready"]) == 0


def submit(cli, spellbook, tmp_path, data):
    path = tmp_path / "assessment.json"
    path.write_text(json.dumps(data))
    return cli(["-C", str(spellbook), "readiness", "assess", "--input", str(path)])


def target_for(spellbook):
    from golden_thread import manifest as manifest_mod

    return readiness.resolve(spellbook, manifest_mod.read(spellbook))


# --- rubric ------------------------------------------------------------


def test_the_rubric_is_published_with_its_thresholds_and_its_caveat(
    cli, dor_source, spellbook, mission, capsys
):
    """An assessor works from policy, not from what it remembers."""
    attach(cli, spellbook, dor_source)
    capsys.readouterr()

    assert cli(["-C", str(spellbook), "readiness", "rubric"]) == 0
    out = capsys.readouterr().out
    assert "spec-readiness@1.0.0" in out
    assert "score >= 8" in out
    assert "a human decision is required" in out
    assert "An assessment, not a measurement." in out


def test_the_json_rubric_carries_everything_an_assessor_needs(
    cli, dor_source, spellbook, mission, capsys
):
    attach(cli, spellbook, dor_source)
    capsys.readouterr()

    cli(["-C", str(spellbook), "readiness", "rubric", "--json"])
    document = json.loads(capsys.readouterr().out)

    assert document["rubric"] == "spec-readiness@1.0.0"
    assert document["thresholds"] == {
        "minScore": 8, "maxBlockers": 0, "requiresHumanApproval": True
    }
    assert {d["id"] for d in document["dimensions"]} == {"problem", "outcome", "scope"}
    assert sum(d["points"] for d in document["dimensions"]) == document["scaleMax"]
    assert document["subjectFiles"] == ["MISSION.md"]
    assert "measurement" in document["caveat"]


def test_a_profile_without_a_readiness_requirement_says_so(
    cli, corporate_source, spellbook, capsys
):
    assert cli(["-C", str(spellbook), "init", "--source", str(corporate_source),
                "--ref", "v0.1.0"]) == 0
    assert cli(["-C", str(spellbook), "readiness", "rubric"]) == 2
    assert "enforces no readiness requirement" in capsys.readouterr().err


# --- assess: the submission is checked, not trusted --------------------


def test_dimensions_must_add_up_to_the_headline_score(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    """9/10 over dimensions summing to 6 is refused, so the number has an argument."""
    attach(cli, spellbook, dor_source)
    inflated = assessment(score=6)
    inflated["score"] = 9

    assert submit(cli, spellbook, tmp_path, inflated) == 2
    assert "add up to 6" in capsys.readouterr().err
    assert state.load_attestations(spellbook) == []


def test_a_dimension_may_not_exceed_what_the_rubric_says_it_is_worth(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    attach(cli, spellbook, dor_source)
    over = assessment(score=10)
    over["dimensions"] = [
        {"id": "problem", "score": 7, "note": "x"},
        {"id": "outcome", "score": 2, "note": "x"},
        {"id": "scope", "score": 1, "note": "x"},
    ]

    assert submit(cli, spellbook, tmp_path, over) == 2
    assert "worth 0 to 4 point(s)" in capsys.readouterr().err


def test_the_dimensions_must_be_the_rubrics_own(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    attach(cli, spellbook, dor_source)
    invented = assessment(score=9)
    invented["dimensions"][2] = {"id": "vibes", "score": 2, "note": "felt right"}

    assert submit(cli, spellbook, tmp_path, invented) == 2
    error = capsys.readouterr().err
    assert "missing dimension(s) scope" in error
    assert "unknown dimension(s) vibes" in error


@pytest.mark.parametrize(
    "section",
    ["facts", "assumptions", "unknowns", "unknownUnknowns", "blockers", "decisions"],
)
def test_every_section_is_required_even_when_empty(
    cli, dor_source, spellbook, mission, tmp_path, capsys, section
):
    """An empty list is an answer. A missing key is a question nobody asked."""
    attach(cli, spellbook, dor_source)
    incomplete = assessment(score=9)
    del incomplete[section]

    assert submit(cli, spellbook, tmp_path, incomplete) == 2
    assert section in capsys.readouterr().err


def test_an_assessment_must_name_its_assessor(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    attach(cli, spellbook, dor_source)
    anonymous = assessment(score=9)
    anonymous["assessor"] = "  "

    assert submit(cli, spellbook, tmp_path, anonymous) == 2
    assert "cannot be weighed" in capsys.readouterr().err


def test_an_assessment_claiming_the_wrong_rubric_is_refused(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    attach(cli, spellbook, dor_source)
    wrong = assessment(score=9)
    wrong["rubric"] = "spec-readiness@0.9.0"

    assert submit(cli, spellbook, tmp_path, wrong) == 2
    assert "this profile pins 'spec-readiness@1.0.0'" in capsys.readouterr().err


def test_a_valid_assessment_is_recorded_with_its_provenance(
    cli, dor_source, spellbook, mission, tmp_path
):
    attach(cli, spellbook, dor_source)
    assert submit(cli, spellbook, tmp_path, assessment(score=9)) == 0

    recorded = state.load_attestations(spellbook, "DOR-001")[0]
    assert recorded.score == 9
    assert recorded.rubric == "spec-readiness@1.0.0"
    assert recorded.actor == "a model, in a test"
    assert recorded.subject.digest == target_for(spellbook).subject.digest


def test_a_later_assessment_replaces_the_earlier_one(
    cli, dor_source, spellbook, mission, tmp_path
):
    attach(cli, spellbook, dor_source)
    submit(cli, spellbook, tmp_path, assessment(score=6))
    submit(cli, spellbook, tmp_path, assessment(score=9))

    claims = state.load_attestations(spellbook, "DOR-001")
    assert len(claims) == 1
    assert claims[0].score == 9


# --- approve: a deliberate act, tied to a specific text ----------------


def test_approval_refuses_when_there_is_no_terminal_and_no_confirmation(
    cli, dor_source, spellbook, mission, tmp_path, capsys, monkeypatch
):
    """The tests themselves run without a terminal, which is the point."""
    attach(cli, spellbook, dor_source)
    submit(cli, spellbook, tmp_path, assessment(score=9))

    assert cli(["-C", str(spellbook), "readiness", "approve"]) == 2
    assert "approval needs a person" in capsys.readouterr().err
    assert state.latest_attestation(spellbook, "DOR-001", HUMAN_ATTESTATION) is None


def test_the_confirmation_phrase_is_tied_to_the_text_being_approved(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    """A phrase copied from an earlier session does not approve a later mission."""
    attach(cli, spellbook, dor_source)
    submit(cli, spellbook, tmp_path, assessment(score=9))
    stale_phrase = readiness.challenge(target_for(spellbook))

    mission.write_text("# Mission\n\nSomething else entirely.\n")
    submit(cli, spellbook, tmp_path, assessment(score=9))

    assert cli(["-C", str(spellbook), "readiness", "approve",
                "--confirm", stale_phrase]) == 2
    assert "does not match" in capsys.readouterr().err
    assert state.latest_attestation(spellbook, "DOR-001", HUMAN_ATTESTATION) is None


def test_there_is_nothing_to_approve_before_an_assessment_exists(
    cli, dor_source, spellbook, mission, capsys
):
    """Approval is a decision on a reading, so there must be a reading."""
    attach(cli, spellbook, dor_source)
    assert cli(["-C", str(spellbook), "readiness", "approve",
                "--confirm", "approve whatever"]) == 2
    assert "no readiness assessment to decide on" in capsys.readouterr().err


def test_approving_an_assessment_of_older_text_is_refused(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    attach(cli, spellbook, dor_source)
    submit(cli, spellbook, tmp_path, assessment(score=9))
    mission.write_text("# Mission\n\nRewritten after the assessment.\n")

    phrase = readiness.challenge(target_for(spellbook))
    assert cli(["-C", str(spellbook), "readiness", "approve", "--confirm", phrase]) == 2
    assert "Re-assess before deciding" in capsys.readouterr().err


def test_the_attestor_is_recorded(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    attach(cli, spellbook, dor_source)
    submit(cli, spellbook, tmp_path, assessment(score=9))
    phrase = readiness.challenge(target_for(spellbook))

    assert cli(["-C", str(spellbook), "readiness", "approve", "--confirm", phrase,
                "--attestor", "owner@academy.invalid", "--note", "answered"]) == 0

    recorded = state.latest_attestation(spellbook, "DOR-001", HUMAN_ATTESTATION)
    assert recorded.actor == "owner@academy.invalid"
    assert recorded.payload == {"decision": "approved", "note": "answered"}


def test_the_person_is_shown_what_they_are_deciding_before_they_decide(
    cli, dor_source, spellbook, mission, tmp_path, capsys
):
    """An approval nobody was informed for would be worth nothing."""
    attach(cli, spellbook, dor_source)
    submit(cli, spellbook, tmp_path,
           assessment(score=9, decisions=["which element?"]))
    phrase = readiness.challenge(target_for(spellbook))
    capsys.readouterr()

    cli(["-C", str(spellbook), "readiness", "approve", "--confirm", phrase])
    out = capsys.readouterr().out
    assert "9/10" in out
    assert "which element?" in out
    assert "it has approved nothing" in out
