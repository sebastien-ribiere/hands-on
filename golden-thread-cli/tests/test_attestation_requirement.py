"""COOKIE-001: the requirement no tool can check, and the command for it.

Two things are being pinned here. That the engine reports honestly on a claim
it can never make itself, and that the `attest` command cannot record one
without a deliberate act tied to this exact version of the work.
"""

import json

import pytest
from golden_thread_testkit import rule

from golden_thread import attest as attest_mod
from golden_thread import manifest as manifest_mod
from golden_thread import state
from golden_thread.attestation import ATTESTED, REFUSED
from golden_thread.checks import human_attestation
from golden_thread.errors import GoldenThreadError
from golden_thread.paths import ATTESTATIONS_NAME
from golden_thread.results import ERROR, FAIL, PASS


def a_rule(**overrides):
    params = {
        "statement": "Cookies have been prepared and shared with the team.",
        "subject_root": "src",
        "subject_globs": ["**/*.py"],
    }
    params.update(overrides)
    return rule("COOKIE-001", human_attestation.NAME, **params)


def a_target(project):
    return attest_mod.Target(
        a_rule(), a_rule().params["statement"], human_attestation.subject(a_rule(), project)
    )


# --- the engine ---------------------------------------------------------


def test_with_nothing_on_record_it_fails_and_says_nothing_can_fix_that(spellbook):
    result = human_attestation.run(a_rule(), spellbook)
    assert result.status == FAIL
    assert any("nobody has attested this" in note for note in result.notes)
    assert any("golden-thread attest COOKIE-001" in note for note in result.notes)


def test_the_claim_is_shown_whatever_the_verdict(spellbook):
    result = human_attestation.run(a_rule(), spellbook)
    assert any("Cookies have been prepared" in note for note in result.notes)


def test_an_attestation_satisfies_it(spellbook):
    attest_mod.record(spellbook, a_target(spellbook), ATTESTED, "seb@academy.invalid")
    result = human_attestation.run(a_rule(), spellbook)
    assert result.status == PASS
    assert any("attested by seb@academy.invalid" in note for note in result.notes)


def test_a_pass_still_says_what_was_actually_established(spellbook):
    attest_mod.record(spellbook, a_target(spellbook), ATTESTED, "seb@academy.invalid")
    result = human_attestation.run(a_rule(), spellbook)
    assert any("not that it happened" in note for note in result.notes)


def test_the_attestation_is_named_in_the_evidence_it_supports(spellbook):
    """A requirement satisfied by a claim never appears without it."""
    attest_mod.record(spellbook, a_target(spellbook), ATTESTED, "seb@academy.invalid")
    result = human_attestation.run(a_rule(), spellbook)
    assert [a.actor for a in result.supporting] == ["seb@academy.invalid"]


def test_a_refusal_is_not_an_attestation(spellbook):
    attest_mod.record(
        spellbook, a_target(spellbook), REFUSED, "seb@academy.invalid", "no oven"
    )
    result = human_attestation.run(a_rule(), spellbook)
    assert result.status == FAIL
    assert any("refused" in note and "no oven" in note for note in result.notes)


def test_the_claim_expires_when_the_work_changes(spellbook):
    """New work, new cookies. A claim is tied to what it was made about."""
    attest_mod.record(spellbook, a_target(spellbook), ATTESTED, "seb@academy.invalid")
    (spellbook / "src" / "spells" / "elements" / "air.py").write_text("x = 9\n")

    result = human_attestation.run(a_rule(), spellbook)
    assert result.status == FAIL
    assert any("different version of the work" in note for note in result.notes)


def test_a_rule_with_no_statement_is_error(spellbook):
    broken = rule(
        "COOKIE-001",
        human_attestation.NAME,
        subject_root="src",
        subject_globs=["**/*.py"],
    )
    result = human_attestation.run(broken, spellbook)
    assert result.status == ERROR
    assert "statement" in result.error


# --- where the record lives --------------------------------------------


def test_attestations_are_committed_not_cached(spellbook):
    """The one artefact nothing can regenerate does not live in the cache.

    Everything in .golden-thread/ is rebuildable: `verify` reproduces the
    evidence, the manifest reproduces the policy. An attestation is somebody's
    word, and it also has to reach a CI runner.
    """
    attest_mod.record(spellbook, a_target(spellbook), ATTESTED, "seb@academy.invalid")

    assert (spellbook / ATTESTATIONS_NAME).is_file()
    assert not (spellbook / ".golden-thread" / "attestations.json").exists()


def test_the_recorded_claim_carries_its_provenance(spellbook):
    attest_mod.record(
        spellbook, a_target(spellbook), ATTESTED, "seb@academy.invalid", "24 of them"
    )
    data = json.loads((spellbook / ATTESTATIONS_NAME).read_text())
    recorded = data["attestations"][0]

    assert recorded["requirement"] == "COOKIE-001"
    assert recorded["provider"] == "human"
    assert recorded["actor"] == "seb@academy.invalid"
    assert recorded["payload"]["note"] == "24 of them"
    assert recorded["payload"]["statement"].startswith("Cookies have been prepared")
    assert recorded["subject"]["digest"].startswith("sha256:")


def test_no_rubric_is_borrowed_to_look_more_rigorous(spellbook):
    """Nothing measured this. The summary says so rather than naming a rubric."""
    attest_mod.record(spellbook, a_target(spellbook), ATTESTED, "seb@academy.invalid")
    recorded = state.latest_attestation(spellbook, "COOKIE-001", "human-attestation")
    assert recorded.rubric == ""
    assert "on their own word" in recorded.summary()


# --- the confirmation discipline ---------------------------------------


def test_the_phrase_is_tied_to_this_version_of_the_work(spellbook):
    before = attest_mod.challenge(a_target(spellbook))
    (spellbook / "src" / "spells" / "elements" / "air.py").write_text("x = 9\n")
    assert attest_mod.challenge(a_target(spellbook)) != before


def test_a_phrase_from_another_version_does_not_confirm(spellbook):
    stale = attest_mod.challenge(a_target(spellbook))
    (spellbook / "src" / "spells" / "elements" / "air.py").write_text("x = 9\n")

    with pytest.raises(GoldenThreadError, match="does not match"):
        attest_mod.confirm(a_target(spellbook), stale)


def test_with_no_terminal_it_refuses_rather_than_assumes(spellbook, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)
    with pytest.raises(GoldenThreadError, match="needs a person"):
        attest_mod.confirm(a_target(spellbook), None)


def test_the_right_phrase_confirms(spellbook):
    target = a_target(spellbook)
    attest_mod.confirm(target, attest_mod.challenge(target))


# --- resolving the requirement from policy, never by id ------------------


def test_a_profile_with_no_attested_requirement_says_so(spellbook, corporate_source, cli):
    cli(["-C", str(spellbook), "init", "--source", str(corporate_source), "--ref", "v0.1.0"])
    manifest = manifest_mod.read(spellbook)
    with pytest.raises(GoldenThreadError, match="nothing to attest"):
        attest_mod.resolve(spellbook, manifest)
