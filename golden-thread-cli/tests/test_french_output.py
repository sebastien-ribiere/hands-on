"""The display language must not change evidence, policy or human authority."""

import json
import shutil
from pathlib import Path

import pytest

from golden_thread_testkit import git
from golden_thread import state
from golden_thread.paths import ATTESTATIONS_NAME
from golden_thread.ui import recorded_text, t

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def french_project(tmp_path, spellbook, cli, monkeypatch, capsys):
    source = tmp_path / "academy-policy"
    shutil.copytree(REPO / "golden-thread-source", source)
    git("init", "-q", "-b", "main", ".", cwd=source)
    git("add", "-A", cwd=source)
    git("commit", "-q", "-m", "Test policy", cwd=source)
    git("tag", "v0.3.0", cwd=source)
    monkeypatch.setenv("GOLDEN_THREAD_LANG", "fr")
    assert cli(["-C", str(spellbook), "init", "--source", str(source),
                "--ref", "v0.3.0", "--profile", "academy-spells-done"]) == 0
    assert "Projet rattaché" in capsys.readouterr().out
    (spellbook / "MISSION.md").write_text("# Mission\nCréer Frost Ward.\n")
    return spellbook


def test_french_rubric_is_a_view_of_the_same_policy(french_project, cli, monkeypatch, capsys):
    args = ["-C", str(french_project), "readiness", "rubric"]
    assert cli(args) == 0
    out = capsys.readouterr().out
    assert "Cette mission est-elle prête" in out
    assert "Les décisions humaines" in out
    assert "ÉVALUATION, pas une mesure" in out
    assert "décision humaine obligatoire" in out
    assert cli(args + ["--json"]) == 0
    fr = capsys.readouterr().out
    monkeypatch.setenv("GOLDEN_THREAD_LANG", "en")
    assert cli(args + ["--json"]) == 0
    assert capsys.readouterr().out == fr
    assert json.loads(fr)["rubricTitle"] == "Is this mission ready to be worked on?"


@pytest.mark.skipif(shutil.which("bandit") is None, reason="real Bandit required")
def test_b307_and_json_stay_raw_while_human_output_is_french(french_project, cli, monkeypatch, capsys):
    probe = french_project / "src/spells/protection/security_probe.py"
    probe.write_text("def improvise(value):\n    return eval(value)\n")
    args = ["-C", str(french_project)]
    exit_fr = cli(args + ["verify"])
    out = capsys.readouterr().out
    assert "FAIL   SEC-001  Aucun défaut de sécurité signalé" in out
    assert "MEDIUM B307 (bandit): Use of possibly insecure function" in out
    assert "Lecture : usage potentiellement dangereux de eval()." in out
    assert "seuil d’échec : sévérité MEDIUM" in out
    assert "aucune approbation humaine enregistrée" in out
    assert "personne ne l’a attesté" in out
    records = [e.to_dict() for e in state.load(french_project).values()]
    assert cli(args + ["status", "--json"]) == exit_fr
    json_fr = capsys.readouterr().out
    monkeypatch.setenv("GOLDEN_THREAD_LANG", "en")
    assert cli(args + ["status", "--json"]) == exit_fr
    assert capsys.readouterr().out == json_fr
    assert [e.to_dict() for e in state.load(french_project).values()] == records
    report = json.loads(json_fr)
    sec = next(r for r in report["requirements"] if r["requirement"] == "SEC-001")
    assert sec["title"] == "No known security defect at MEDIUM or above"
    assert sec["evidence"]["result"]["findings"][0]["rule"] == "B307"
    # Removing the temporary defect invalidates the old proof in either language.
    probe.unlink()
    monkeypatch.setenv("GOLDEN_THREAD_LANG", "fr")
    cli(args + ["status"])
    assert "le code a changé" in capsys.readouterr().out
    cli(args + ["verify", "--json"])
    report = json.loads(capsys.readouterr().out)
    assert next(r for r in report["requirements"] if r["requirement"] == "SEC-001")["reportedStatus"] == "PASS"


def test_display_and_wrong_confirmation_never_create_attestation(french_project, cli, capsys):
    args = ["-C", str(french_project), "attest", "COOKIE-001"]
    assert cli(args + ["--show"]) == 0
    shown = capsys.readouterr().out
    assert "Des cookies ont été préparés" in shown
    assert "--confirm 'attest " in shown
    assert "Rien n’a été enregistré" in shown
    assert not (french_project / ATTESTATIONS_NAME).exists()
    assert cli(args + ["--confirm", "incorrect"]) == 2
    assert "la confirmation ne correspond pas" in capsys.readouterr().err
    assert not (french_project / ATTESTATIONS_NAME).exists()


def test_unknown_wording_and_captured_user_content_are_not_rewritten(monkeypatch):
    monkeypatch.setenv("GOLDEN_THREAD_LANG", "fr")
    assert t("An organisation's custom requirement") == "An organisation's custom requirement"
    assert recorded_text("A custom diagnostic") == "A custom diagnostic"
    assert recorded_text("approved by Profile") == "approbation enregistrée par Profile"
    assert recorded_text("the requirement changed: abc -> def") == "l’exigence a changé : abc -> def"
    assert t("Type the phrase to confirm: {0}", "approve abc123") == "Saisissez la phrase pour confirmer : approve abc123"
