"""The evidence model: what a claim must carry before it may be believed."""

import json

from golden_thread.paths import evidence_path

FIVE_QUESTIONS = {"requirement", "subject", "producer", "method", "result"}


def _init(cli, source, project, ref="v0.1.0"):
    return cli(["-C", str(project), "init", "--source", str(source), "--ref", ref])


def _json(cli, project, command, capsys):
    code = cli(["-C", str(project), command, "--json"])
    return code, json.loads(capsys.readouterr().out)


def test_evidence_answers_the_five_questions(cli, corporate_source, spellbook):
    _init(cli, corporate_source, spellbook)
    cli(["-C", str(spellbook), "verify"])

    record = json.loads(evidence_path(spellbook).read_text())["evidence"][0]
    assert FIVE_QUESTIONS <= set(record)
    assert record["timestamp"]

    assert record["requirement"] == "ARCH-001"
    assert record["subject"]["kind"] == "worktree"
    assert record["subject"]["root"] == "src"
    assert record["subject"]["digest"].startswith("sha256:")
    assert record["subject"]["fileCount"] > 0
    assert record["producer"]["name"] == "golden-thread"
    assert record["producer"]["version"]
    assert record["method"]["check"] == "layered_dependencies"
    assert record["method"]["profile"] == "academy-spells"
    assert record["method"]["policyRef"] == "v0.1.0"
    assert len(record["method"]["policyRevision"]) == 40
    assert record["result"]["status"] == "PASS"


def test_no_status_is_ever_reported_without_its_provenance(
    cli, corporate_source, spellbook, capsys
):
    """The acceptance criterion, as an executable statement.

    There is no `architecture: true` anywhere: every reported status in the
    report is anchored to a requirement, a subject, a producer and a method.
    """
    _init(cli, corporate_source, spellbook)
    cli(["-C", str(spellbook), "verify"])
    capsys.readouterr()

    _, report = _json(cli, spellbook, "status", capsys)

    flat = json.dumps(report)
    assert "architecture" not in flat.lower()

    assert report["pathStatus"] == "ON PATH"
    for item in report["requirements"]:
        assert item["reportedStatus"] == "PASS"
        evidence = item["evidence"]
        assert evidence["requirement"] == item["requirement"]
        assert evidence["subject"]["digest"]
        assert evidence["producer"]["name"]
        assert evidence["method"]["policyRevision"]


def test_human_output_carries_the_same_provenance(
    cli, corporate_source, spellbook, capsys
):
    _init(cli, corporate_source, spellbook)
    cli(["-C", str(spellbook), "verify"])
    capsys.readouterr()

    assert cli(["-C", str(spellbook), "status"]) == 0
    out = capsys.readouterr().out
    assert "PASS   ARCH-001" in out
    assert "subject   src/" in out
    assert "sha256:" in out
    assert "method    layered_dependencies" in out
    assert "producer  golden-thread" in out
    assert "PATH STATUS   ON PATH" in out


def test_the_json_report_is_a_single_document_on_stdout(
    cli, corporate_source, spellbook, capsys
):
    _init(cli, corporate_source, spellbook)
    capsys.readouterr()

    code, report = _json(cli, spellbook, "verify", capsys)
    assert code == 0
    assert report["command"] == "verify"
    assert report["exitCode"] == 0
    assert report["goldenThread"]["ref"] == "v0.1.0"


def test_verify_records_one_record_per_requirement(cli, corporate_source, spellbook):
    _init(cli, corporate_source, spellbook)
    cli(["-C", str(spellbook), "verify"])
    cli(["-C", str(spellbook), "verify"])

    stored = json.loads(evidence_path(spellbook).read_text())["evidence"]
    assert len(stored) == 1  # latest state, not an audit journal


def test_the_subject_digest_is_stable_across_runs(cli, corporate_source, spellbook):
    _init(cli, corporate_source, spellbook)
    cli(["-C", str(spellbook), "verify"])
    first = json.loads(evidence_path(spellbook).read_text())["evidence"][0]
    cli(["-C", str(spellbook), "verify"])
    second = json.loads(evidence_path(spellbook).read_text())["evidence"][0]

    assert first["subject"]["digest"] == second["subject"]["digest"]


def test_a_failing_run_still_produces_full_evidence(cli, corporate_source, spellbook):
    """A failure is a claim too, and needs the same provenance as a pass."""
    _init(cli, corporate_source, spellbook)
    ward = spellbook / "src" / "spells" / "protection" / "ward.py"
    ward.write_text(ward.read_text() + "\nfrom ..elements import fire\n")

    assert cli(["-C", str(spellbook), "verify"]) == 1
    record = json.loads(evidence_path(spellbook).read_text())["evidence"][0]
    assert record["result"]["status"] == "FAIL"
    assert record["result"]["violations"][0]["targetModule"] == "spells.elements.fire"
    assert record["subject"]["digest"]
    assert record["method"]["policyRevision"]


def test_unreadable_evidence_is_no_evidence_rather_than_a_verdict(
    cli, corporate_source, spellbook, capsys
):
    _init(cli, corporate_source, spellbook)
    cli(["-C", str(spellbook), "verify"])
    evidence_path(spellbook).write_text("{ not json")
    capsys.readouterr()

    assert cli(["-C", str(spellbook), "status"]) == 0
    assert "PATH STATUS   INCOMPLETE" in capsys.readouterr().out
