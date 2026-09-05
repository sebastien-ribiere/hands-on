"""The vertical slice, driven through the CLI exactly as a developer would."""

import json
import subprocess

from golden_thread import manifest as manifest_mod
from golden_thread.paths import evidence_path, source_dir


def _run(cli, *args):
    return cli(list(args))


def test_init_records_the_ref_and_the_resolved_commit(cli, corporate_source, spellbook, capsys):
    assert _run(cli, "-C", str(spellbook), "init",
                "--source", str(corporate_source), "--ref", "v0.1.0") == 0

    manifest = manifest_mod.read(spellbook)
    assert manifest.ref == "v0.1.0"
    assert manifest.profile == "academy-spells"

    expected = subprocess.run(
        ["git", "rev-parse", "v0.1.0^{commit}"],
        cwd=str(corporate_source), capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert manifest.revision == expected
    assert len(manifest.revision) == 40


def test_verify_reports_policy_from_init_not_cli_version(
    cli, corporate_source, spellbook, capsys
):
    _run(cli, "-C", str(spellbook), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0")
    capsys.readouterr()
    assert _run(cli, "-C", str(spellbook), "verify") == 0
    out = capsys.readouterr().out
    assert "Policy ref    v0.1.0" in out
    assert "Profile       academy-spells" in out
    assert "tool      golden-thread 0.3.0" in out


def test_init_next_preserves_project(cli, corporate_source, spellbook, capsys):
    _run(cli, "-C", str(spellbook), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0")
    out = capsys.readouterr().out
    assert f"Next          golden-thread -C {spellbook} verify" in out


def test_manifest_stays_minimal(cli, corporate_source, spellbook):
    _run(cli, "-C", str(spellbook), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0")
    data = json.loads((spellbook / "golden-thread.json").read_text())
    assert set(data) == {"manifestVersion", "source", "ref", "revision", "profile"}


def test_corporate_config_is_not_copied_into_the_project(cli, corporate_source, spellbook):
    """Only the cache holds the policy, and the cache is ignored."""
    _run(cli, "-C", str(spellbook), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0")

    tracked = [
        p for p in spellbook.rglob("*.toml")
        if ".golden-thread" not in p.parts
    ]
    assert tracked == []
    assert ".golden-thread/" in (spellbook / ".gitignore").read_text()


def test_status_is_incomplete_before_any_verify(cli, corporate_source, spellbook, capsys):
    _run(cli, "-C", str(spellbook), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0")
    capsys.readouterr()

    assert _run(cli, "-C", str(spellbook), "status") == 0
    out = capsys.readouterr().out
    assert "Policy ref    v0.1.0" in out
    assert "Profile       academy-spells" in out
    assert "UNKNOWN ARCH-001" in out
    assert "never verified" in out
    assert "PATH STATUS   INCOMPLETE" in out


def test_full_cycle_on_path_then_off_path_then_back(cli, corporate_source, spellbook, capsys):
    _run(cli, "-C", str(spellbook), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0")

    # 1. compliant
    assert _run(cli, "-C", str(spellbook), "verify") == 0
    capsys.readouterr()
    assert _run(cli, "-C", str(spellbook), "status") == 0
    assert "PATH STATUS   ON PATH" in capsys.readouterr().out

    # 2. a protection spell reaches into Fire
    ward = spellbook / "src" / "spells" / "protection" / "ward.py"
    compliant = ward.read_text()
    ward.write_text(compliant + "\nfrom ..elements import fire\n")

    assert _run(cli, "-C", str(spellbook), "verify") == 1
    out = capsys.readouterr().out
    assert "FAIL   ARCH-001" in out
    assert "spells.elements.fire" in out
    assert "PATH STATUS   OFF PATH" in out

    assert _run(cli, "-C", str(spellbook), "status") == 1
    assert "PATH STATUS   OFF PATH" in capsys.readouterr().out

    # 3. deviation removed
    ward.write_text(compliant)
    assert _run(cli, "-C", str(spellbook), "verify") == 0
    capsys.readouterr()
    assert _run(cli, "-C", str(spellbook), "status") == 0
    assert "PATH STATUS   ON PATH" in capsys.readouterr().out


def test_status_reports_recorded_evidence(cli, corporate_source, spellbook):
    _run(cli, "-C", str(spellbook), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0")
    _run(cli, "-C", str(spellbook), "verify")

    recorded = json.loads(evidence_path(spellbook).read_text())["evidence"]
    assert [e["requirement"] for e in recorded] == ["ARCH-001"]
    assert recorded[0]["result"]["status"] == "PASS"
    assert recorded[0]["method"]["policyRevision"] == manifest_mod.read(spellbook).revision


def test_cache_is_restored_from_the_manifest_alone(cli, corporate_source, spellbook):
    """A fresh clone of the project has a manifest but no cache."""
    import shutil

    _run(cli, "-C", str(spellbook), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0")
    revision = manifest_mod.read(spellbook).revision
    shutil.rmtree(source_dir(spellbook))

    assert _run(cli, "-C", str(spellbook), "verify") == 0
    restored = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(source_dir(spellbook)),
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert restored == revision


def test_status_without_a_manifest_fails_with_guidance(cli, spellbook, capsys):
    assert _run(cli, "-C", str(spellbook), "status") == 2
    assert "golden-thread init" in capsys.readouterr().err


def test_init_with_an_unknown_ref_fails_cleanly(cli, corporate_source, spellbook, capsys):
    assert _run(cli, "-C", str(spellbook), "init",
                "--source", str(corporate_source), "--ref", "v9.9.9") == 2
    assert not (spellbook / "golden-thread.json").exists()


def test_init_with_an_unknown_profile_fails_before_writing_a_manifest(
    cli, corporate_source, spellbook, capsys
):
    assert _run(cli, "-C", str(spellbook), "init", "--source", str(corporate_source),
                "--ref", "v0.1.0", "--profile", "nope") == 2
    assert "unknown profile" in capsys.readouterr().err
    assert not (spellbook / "golden-thread.json").exists()
