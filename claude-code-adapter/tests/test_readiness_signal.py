"""How the adapter surfaces a Definition of Ready.

Two things are being pinned. First, that NOT READY reaches a session at all,
and reaches it in its own words: "you are leaving the supported path" is the
wrong sentence for work nobody has agreed to yet, and the adapter must not
reuse it. Second -- and this is the one that matters -- that surfacing a DoR
does not turn the adapter into a gate. Everything Spike 3 proved about the
hooks being unable to block still holds with a readiness requirement failing.
"""

import subprocess
import sys
from pathlib import Path

from conftest import GOLDEN_THREAD_BIN, verify

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from render import context_lines, deviation_lines  # noqa: E402


def status_report(project_dir):
    import json

    proc = subprocess.run(
        [GOLDEN_THREAD_BIN, "-C", str(project_dir), "status", "--json"],
        capture_output=True, text=True,
    )
    return json.loads(proc.stdout)


def test_a_session_opens_knowing_the_work_is_not_ready(attached_with_dor):
    verify(attached_with_dor)
    lines = context_lines(status_report(attached_with_dor))

    assert "Status: NOT READY" in lines
    assert any("DOR-001" in line for line in lines)
    # The core's own reason, carried through rather than reworded.
    assert any("no human approval on record" in line for line in lines)


def test_not_ready_is_not_described_as_a_deviation(attached_with_dor):
    verify(attached_with_dor)
    lines = deviation_lines(status_report(attached_with_dor))

    assert lines[0] == "GOLDEN THREAD -- NOT READY"
    assert "This work has not met its Definition of Ready." in lines
    assert not any("leaving the supported path" in line for line in lines)
    assert "Do not start implementation silently while NOT READY." in lines
    assert any("explicitly choose to continue off-path" in line for line in lines)
    assert any("agent discipline, not a technical gate" in line for line in lines)


def test_an_architecture_deviation_still_reads_as_one(attached):
    """The new wording is scoped to NOT READY and did not swallow the old one."""
    from conftest import break_arch_001

    break_arch_001(attached)
    verify(attached)
    lines = deviation_lines(status_report(attached))

    assert lines[0] == "GOLDEN THREAD DEVIATION"
    assert "You are leaving the supported path." in lines


def test_the_edit_is_still_allowed_while_not_ready(attached_with_dor, run_hook):
    """The whole stance, restated for the DoR: it signals, it does not gate."""
    verify(attached_with_dor)
    output = run_hook("pre_tool_use.py", attached_with_dor)

    assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "NOT READY" in context
    assert "Do not start implementation silently" in context
    assert "explicitly choose to continue off-path" in context


def test_nothing_is_said_once_the_mission_is_ready(attached_with_dor, run_hook):
    """Silence is the default. A satisfied DoR is not an announcement."""
    project = attached_with_dor
    import json

    assessment = {
        "assessor": "a model, in a test",
        "rubric": "spec-readiness@1.0.0",
        "score": 9,
        "dimensions": [{"id": "problem", "score": 9, "note": "clear"}],
        "facts": [], "assumptions": [], "unknowns": [],
        "unknownUnknowns": [], "blockers": [], "decisions": [],
    }
    (project / "assessment.json").write_text(json.dumps(assessment))
    subprocess.run(
        [GOLDEN_THREAD_BIN, "-C", str(project), "readiness", "assess",
         "--input", str(project / "assessment.json")],
        capture_output=True, text=True, check=True,
    )
    digest = status_report(project)  # noqa: F841 - forces the manifest to exist
    phrase_proc = subprocess.run(
        [GOLDEN_THREAD_BIN, "-C", str(project), "readiness", "rubric", "--json"],
        capture_output=True, text=True, check=True,
    )
    short = json.loads(phrase_proc.stdout)["subject"]["digest"][7:19]
    approved = subprocess.run(
        [GOLDEN_THREAD_BIN, "-C", str(project), "readiness", "approve",
         "--attestor", "owner@example.invalid", "--confirm", f"approve {short}"],
        capture_output=True, text=True,
    )
    assert approved.returncode == 0, approved.stderr

    verify(project)
    assert deviation_lines(status_report(project)) is None
    assert run_hook("pre_tool_use.py", project) is None
