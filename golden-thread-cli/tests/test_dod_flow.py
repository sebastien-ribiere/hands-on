"""The Definition of Done as a whole: the profile, the CLI, the report.

The individual engines are tested in their own modules. What is pinned here is
what happens when a profile carries several of them at once -- which status
wins, what the report carries, and what the commands refuse to do.
"""

import json

import pytest
from golden_thread_testkit import publish_dod

from golden_thread import manifest as manifest_mod
from golden_thread.paths import ATTESTATIONS_NAME

DOD = ["TEST-001", "ARCH-001", "DOC-001", "COOKIE-001"]


@pytest.fixture
def done_source(corporate_source):
    """A corporate source whose v0.3.0 publishes a Definition of Done.

    SEC-001 is deliberately left out: it needs bandit installed, and it has its
    own tests. Adding a DoD to a golden path is a policy change and a new tag.
    """
    return publish_dod(corporate_source, DOD)


@pytest.fixture
def attached(spellbook, done_source, cli, capsys):
    (spellbook / "docs").mkdir()
    (spellbook / "docs" / "ARCHITECTURE.md").write_text("# Spellbook\n\nLayers.\n")
    cli([
        "-C", str(spellbook), "init",
        "--source", str(done_source), "--ref", "v0.3.0",
        "--profile", "academy-spells-done",
    ])
    capsys.readouterr()
    return spellbook


def report_of(cli, project, capsys, command="status"):
    cli(["-C", str(project), command, "--json"])
    return json.loads(capsys.readouterr().out)


def status_of(report, requirement):
    for entry in report["requirements"]:
        if entry["requirement"] == requirement:
            return entry["reportedStatus"]
    raise AssertionError(f"{requirement} not in report")


# --- the profile as a contract ------------------------------------------


def test_the_profile_carries_every_requirement_in_order(attached, cli, capsys):
    report = report_of(cli, attached, capsys, "verify")
    assert [r["requirement"] for r in report["requirements"]] == DOD


def test_an_unfinished_project_is_off_path_with_exit_1(attached, cli, capsys):
    assert cli(["-C", str(attached), "verify"]) == 1
    capsys.readouterr()
    report = report_of(cli, attached, capsys)
    assert report["pathStatus"] == "OFF PATH"
    assert report["exitCode"] == 1


def test_the_mechanical_halves_pass_on_their_own(attached, cli, capsys):
    """Nothing is wrong with the code. The project is still not done."""
    report = report_of(cli, attached, capsys, "verify")
    assert status_of(report, "TEST-001") == "PASS"
    assert status_of(report, "ARCH-001") == "PASS"
    assert status_of(report, "DOC-001") == "FAIL"
    assert status_of(report, "COOKIE-001") == "FAIL"


def test_everything_done_is_on_path_with_exit_0(attached, cli, capsys):
    cli(["-C", str(attached), "docs", "stamp"])
    cli([
        "-C", str(attached), "attest", "COOKIE-001",
        "--attestor", "seb@academy.invalid",
        "--confirm", _phrase(cli, attached, capsys),
    ])
    capsys.readouterr()
    assert cli(["-C", str(attached), "verify"]) == 0


def _phrase(cli, project, capsys):
    cli(["-C", str(project), "attest", "COOKIE-001", "--show"])
    shown = capsys.readouterr().out
    return shown.split("--confirm '")[1].split("'")[0]


# --- what the report carries --------------------------------------------


def test_the_report_names_the_command_that_produced_a_verdict(attached, cli, capsys):
    """"external_command" does not describe a method. What ran does."""
    report = report_of(cli, attached, capsys, "verify")
    for entry in report["requirements"]:
        if entry["requirement"] == "TEST-001":
            assert entry["evidence"]["method"]["command"][0] == "python3"


def test_a_requirement_with_no_command_carries_an_empty_one(attached, cli, capsys):
    report = report_of(cli, attached, capsys, "verify")
    for entry in report["requirements"]:
        if entry["requirement"] == "ARCH-001":
            assert entry["evidence"]["method"]["command"] == []


def test_the_report_carries_the_pinned_policy(attached, cli, capsys):
    report = report_of(cli, attached, capsys, "verify")
    assert report["goldenThread"]["ref"] == "v0.3.0"
    assert report["goldenThread"]["profile"] == "academy-spells-done"


# --- commands that must refuse ------------------------------------------


def test_show_records_nothing(attached, cli, capsys):
    cli(["-C", str(attached), "attest", "COOKIE-001", "--show"])
    assert "Nothing was recorded" in capsys.readouterr().out
    assert not (attached / ATTESTATIONS_NAME).exists()


def test_a_wrong_confirmation_records_nothing(attached, cli, capsys):
    assert cli([
        "-C", str(attached), "attest", "COOKIE-001", "--confirm", "attest whatever"
    ]) == 2
    assert not (attached / ATTESTATIONS_NAME).exists()


def test_naming_a_requirement_that_is_not_attestable_is_refused(attached, cli, capsys):
    assert cli(["-C", str(attached), "attest", "ARCH-001", "--confirm", "x"]) == 2
    assert "no attested requirement" in capsys.readouterr().err


# --- the manifest a CI runner reads --------------------------------------


def test_a_relative_source_resolves_against_the_project(spellbook, done_source, cli):
    """What makes the manifest committable, and therefore what makes CI able
    to restore the reviewed policy with no developer present."""
    relative = str(done_source.relative_to(spellbook.parent).as_posix())
    cli([
        "-C", str(spellbook), "init",
        "--source", f"../{relative}", "--ref", "v0.3.0",
        "--profile", "academy-spells-done",
    ])
    manifest = manifest_mod.read(spellbook)

    assert manifest.source == f"../{relative}"
    assert manifest.resolved_source(spellbook) == str(done_source.resolve())


def test_a_url_source_is_left_alone(spellbook):
    manifest = manifest_mod.Manifest(
        source="https://gitlab.example/golden-thread.git",
        ref="v0.3.0", revision="a" * 40, profile="p",
    )
    assert manifest.resolved_source(spellbook) == "https://gitlab.example/golden-thread.git"


def test_the_cache_can_be_deleted_and_the_policy_restored(attached, cli, capsys):
    """A fresh checkout has a manifest and no cache. That is enough."""
    import shutil

    cli(["-C", str(attached), "verify"])
    capsys.readouterr()
    shutil.rmtree(attached / ".golden-thread")

    report = report_of(cli, attached, capsys)
    assert report["goldenThread"]["ref"] == "v0.3.0"
    # The evidence went with the cache; the attestations did not.
    assert all(r["evidence"] is None for r in report["requirements"])
