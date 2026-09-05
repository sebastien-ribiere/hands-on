"""Stale evidence must never be presented as a verdict.

The mechanism under test is the subject digest plus the requirement
fingerprint: a record becomes stale when the work it describes changed, or
when the requirement itself changed. Moving the same requirement between tags
or profiles does not invalidate it.
"""

import json
import subprocess

from conftest import git


def _init(cli, source, project, ref="v0.1.0", profile=None):
    args = ["-C", str(project), "init", "--source", str(source), "--ref", ref]
    if profile:
        args += ["--profile", profile]
    return cli(args)


def _status_json(cli, project, capsys):
    code = cli(["-C", str(project), "status", "--json"])
    return code, json.loads(capsys.readouterr().out)


def _attached_and_on_path(cli, source, project, capsys):
    _init(cli, source, project)
    assert cli(["-C", str(project), "verify"]) == 0
    capsys.readouterr()
    return project


# --- the subject changes -----------------------------------------------------

def test_editing_a_verified_file_makes_the_evidence_stale(
    cli, corporate_source, spellbook, capsys
):
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)

    shield = spellbook / "src" / "spells" / "protection" / "shield.py"
    shield.write_text(shield.read_text() + "\n# a later thought\n")

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 3
    assert report["pathStatus"] == "STALE"
    item = report["requirements"][0]
    assert item["reportedStatus"] == "STALE"
    assert item["freshness"]["state"] == "STALE"
    assert any("the code changed" in r for r in item["freshness"]["reasons"])
    assert (
        item["freshness"]["currentSubjectDigest"]
        != item["evidence"]["subject"]["digest"]
    )


def test_the_old_pass_is_never_presented_as_the_current_verdict(
    cli, corporate_source, spellbook, capsys
):
    """The acceptance criterion, stated on the human output."""
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)
    shield = spellbook / "src" / "spells" / "protection" / "shield.py"
    shield.write_text(shield.read_text() + "\n# a later thought\n")

    assert cli(["-C", str(spellbook), "status"]) == 3
    out = capsys.readouterr().out

    assert "STALE  ARCH-001" in out
    assert "PATH STATUS   STALE" in out
    assert "PATH STATUS   ON PATH" not in out
    # The old result is still shown, but only as history, never as a verdict.
    assert "recorded PASS no longer applies" in out
    assert "the code changed" in out


def test_adding_a_file_to_the_subject_makes_the_evidence_stale(
    cli, corporate_source, spellbook, capsys
):
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)
    (spellbook / "src" / "spells" / "protection" / "aegis.py").write_text("x = 1\n")

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 3
    assert report["pathStatus"] == "STALE"


def test_deleting_a_verified_file_makes_the_evidence_stale(
    cli, corporate_source, spellbook, capsys
):
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)
    (spellbook / "src" / "spells" / "protection" / "shield.py").unlink()

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 3
    assert report["pathStatus"] == "STALE"


def test_a_stale_failure_is_not_reported_as_off_path_either(
    cli, corporate_source, spellbook, capsys
):
    """Staleness cuts both ways: a fixed deviation is not still a deviation."""
    _init(cli, corporate_source, spellbook)
    ward = spellbook / "src" / "spells" / "protection" / "ward.py"
    compliant = ward.read_text()
    ward.write_text(compliant + "\nfrom ..elements import fire\n")

    assert cli(["-C", str(spellbook), "verify"]) == 1
    capsys.readouterr()
    assert cli(["-C", str(spellbook), "status"]) == 1
    capsys.readouterr()

    ward.write_text(compliant)

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 3
    assert report["pathStatus"] == "STALE"
    assert report["requirements"][0]["evidence"]["result"]["status"] == "FAIL"
    assert report["requirements"][0]["reportedStatus"] == "STALE"


# --- the subject does not change ---------------------------------------------

def test_editing_a_file_the_rule_never_read_does_not_invalidate(
    cli, corporate_source, spellbook, capsys
):
    """The digest covers what was inspected, not the whole worktree."""
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)

    (spellbook / "README.md").write_text("# Spellbook\n\nNotes, not code.\n")
    (spellbook / "docs").mkdir()
    (spellbook / "docs" / "guide.md").write_text("prose\n")

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 0
    assert report["pathStatus"] == "ON PATH"
    assert report["requirements"][0]["freshness"]["state"] == "FRESH"


def test_touching_a_file_without_changing_it_does_not_invalidate(
    cli, corporate_source, spellbook, capsys
):
    """Content, not mtime: rewriting identical bytes is not a change."""
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)
    shield = spellbook / "src" / "spells" / "protection" / "shield.py"
    shield.write_text(shield.read_text())

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 0
    assert report["pathStatus"] == "ON PATH"


# --- the requirement changes ------------------------------------------------

def test_changing_a_requirement_makes_its_evidence_stale(
    cli, corporate_source, spellbook, capsys
):
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)

    rule = corporate_source / "rules" / "ARCH-001.toml"
    rule.write_text(rule.read_text().replace('name = "protection"', 'name = "wards"'))
    git("add", "-A", cwd=corporate_source)
    git("commit", "-q", "-m", "change ARCH-001", cwd=corporate_source)
    git("tag", "v0.2.0", cwd=corporate_source)

    _init(cli, corporate_source, spellbook, ref="v0.2.0")
    capsys.readouterr()

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 3
    assert report["pathStatus"] == "STALE"
    reasons = report["requirements"][0]["freshness"]["reasons"]
    assert any("the requirement changed" in r for r in reasons)
    assert not any("the code changed" in r for r in reasons)


def test_moving_unchanged_requirement_to_new_tag_keeps_evidence_fresh(
    cli, corporate_source, spellbook, capsys
):
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)

    (corporate_source / "NOTES.md").write_text("new policy release, ARCH unchanged\n")
    git("add", "-A", cwd=corporate_source)
    git("commit", "-q", "-m", "release v0.2.0", cwd=corporate_source)
    git("tag", "v0.2.0", cwd=corporate_source)

    _init(cli, corporate_source, spellbook, ref="v0.2.0")
    capsys.readouterr()

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 0
    assert report["pathStatus"] == "ON PATH"
    assert report["requirements"][0]["freshness"]["state"] == "FRESH"
    assert report["requirements"][0]["freshness"]["reasons"] == []


def test_moving_unchanged_requirement_to_new_profile_keeps_evidence_fresh(
    cli, corporate_source, spellbook, capsys
):
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)

    (corporate_source / "profiles" / "strict.toml").write_text(
        'name = "strict"\ndescription = "same rules, different profile"\n'
        'rules = ["ARCH-001"]\n'
    )
    git("add", "-A", cwd=corporate_source)
    git("commit", "-q", "-m", "add strict", cwd=corporate_source)
    git("tag", "-f", "v0.1.0", cwd=corporate_source)

    _init(cli, corporate_source, spellbook, profile="strict")
    capsys.readouterr()

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 0
    assert report["pathStatus"] == "ON PATH"
    assert report["requirements"][0]["freshness"]["state"] == "FRESH"


# --- recovering --------------------------------------------------------------

def test_verifying_again_restores_a_current_verdict(
    cli, corporate_source, spellbook, capsys
):
    _attached_and_on_path(cli, corporate_source, spellbook, capsys)
    shield = spellbook / "src" / "spells" / "protection" / "shield.py"
    shield.write_text(shield.read_text() + "\n# a later thought\n")

    assert cli(["-C", str(spellbook), "status"]) == 3
    capsys.readouterr()

    assert cli(["-C", str(spellbook), "verify"]) == 0
    capsys.readouterr()

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 0
    assert report["pathStatus"] == "ON PATH"
    assert report["requirements"][0]["freshness"]["reasons"] == []


def test_verify_is_never_stale_by_construction(
    cli, corporate_source, spellbook, capsys
):
    _init(cli, corporate_source, spellbook)
    shield = spellbook / "src" / "spells" / "protection" / "shield.py"
    shield.write_text(shield.read_text() + "\n# changed just before verifying\n")
    capsys.readouterr()

    cli(["-C", str(spellbook), "verify", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert report["requirements"][0]["freshness"]["state"] == "FRESH"


def test_a_git_revision_is_recorded_when_one_exists_but_is_not_the_mechanism(
    cli, corporate_source, spellbook, capsys
):
    """The digest decides. Git is context, and may legitimately be absent."""
    git("init", "-q", "-b", "main", ".", cwd=spellbook)
    git("add", "-A", cwd=spellbook)
    git("commit", "-q", "-m", "spellbook", cwd=spellbook)

    _attached_and_on_path(cli, corporate_source, spellbook, capsys)
    code, report = _status_json(cli, spellbook, capsys)
    subject = report["requirements"][0]["evidence"]["subject"]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(spellbook),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert subject["gitRevision"] == head
    assert code == 0

    (spellbook / "NOTES.md").write_text("prose\n")
    git("add", "-A", cwd=spellbook)
    git("commit", "-q", "-m", "notes", cwd=spellbook)

    code, report = _status_json(cli, spellbook, capsys)
    assert code == 0
    assert report["pathStatus"] == "ON PATH"
