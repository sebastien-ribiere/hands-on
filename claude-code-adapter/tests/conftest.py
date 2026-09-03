import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ADAPTER = Path(__file__).resolve().parents[1]
HOOKS = ADAPTER / "hooks"

# A bare `golden-thread` on PATH is not guaranteed to be this tool -- see the
# adapter README. Tests pin the exact binary the same way the demo does.
GOLDEN_THREAD_BIN = str(ADAPTER.parent / "golden-thread-cli" / "bin" / "golden-thread")
ENV = {**os.environ, "GOLDEN_THREAD_BIN": GOLDEN_THREAD_BIN}


def git(*args, cwd):
    subprocess.run(
        [
            "git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
            "-c", "user.name=Test", "-c", "user.email=test@local", *args,
        ],
        cwd=str(cwd), check=True, capture_output=True, text=True,
    )


@pytest.fixture
def corporate_source(tmp_path):
    """A minimal Golden Thread source repository, tagged v0.1.0."""
    root = tmp_path / "source"
    (root / "profiles").mkdir(parents=True)
    (root / "rules").mkdir()
    (root / "golden-thread.toml").write_text(
        'schema_version = 1\ndefault_profile = "academy-spells"\n'
    )
    (root / "profiles" / "academy-spells.toml").write_text(
        'name = "academy-spells"\ndescription = "test"\nrules = ["ARCH-001"]\n'
    )
    (root / "rules" / "ARCH-001.toml").write_text(
        'id = "ARCH-001"\n'
        'title = "Protection spells must not depend on Fire"\n'
        'check = "layered_dependencies"\n'
        "[params]\n"
        'source_root = "src"\n'
        "[[params.layers]]\n"
        'name = "protection"\n'
        'match = "spells.protection"\n'
        'allow = ["spells.elements.air", "spells.elements.water"]\n'
        'deny = ["spells.elements.fire"]\n'
    )
    git("init", "-q", "-b", "main", ".", cwd=root)
    git("add", "-A", cwd=root)
    git("commit", "-q", "-m", "v0.1.0", cwd=root)
    git("tag", "v0.1.0", cwd=root)
    return root


@pytest.fixture
def project(tmp_path):
    """A compliant consumer project, not yet attached to Golden Thread."""
    root = tmp_path / "project"
    spells = root / "src" / "spells"
    for package in ("elements", "protection"):
        (spells / package).mkdir(parents=True)
        (spells / package / "__init__.py").write_text("")
    (spells / "__init__.py").write_text("")
    (spells / "elements" / "air.py").write_text("def gust():\n    return 'air'\n")
    (spells / "elements" / "fire.py").write_text("def scorch(t):\n    return t\n")
    (spells / "protection" / "shield.py").write_text(
        "from spells.elements.air import gust\n\n\ndef cast():\n    return gust()\n"
    )
    return root


@pytest.fixture
def attached(project, corporate_source):
    """A project attached to Golden Thread, nothing verified yet."""
    result = subprocess.run(
        [GOLDEN_THREAD_BIN, "-C", str(project), "init",
         "--source", str(corporate_source), "--ref", "v0.1.0"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    return project


def verify(project_dir: Path) -> None:
    subprocess.run(
        [GOLDEN_THREAD_BIN, "-C", str(project_dir), "verify"], capture_output=True, text=True,
    )


def break_arch_001(project_dir: Path) -> None:
    """Make a protection spell reach into Fire."""
    shield = project_dir / "src" / "spells" / "protection" / "shield.py"
    shield.write_text(shield.read_text() + "\nfrom spells.elements import fire\n")


@pytest.fixture
def run_hook():
    """Invoke a hook exactly as Claude Code would: JSON in on stdin, JSON out on stdout."""

    def _run(name: str, project_dir: Path):
        proc = subprocess.run(
            [sys.executable, str(HOOKS / name)],
            input=json.dumps({"cwd": str(project_dir), "hook_event_name": "x"}),
            capture_output=True, text=True, env=ENV,
        )
        assert proc.returncode == 0, proc.stderr
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    return _run


RUBRIC = """
id = "spec-readiness"
version = "1.0.0"
title = "Is this mission ready?"
scale_max = 10
caveat = "An assessment, not a measurement."

[[dimensions]]
id = "problem"
title = "The problem"
points = 10
asks = "Is the problem stated?"
"""

DOR_RULE = """
id = "DOR-001"
title = "A mission is Ready before implementation starts"
check = "spec_readiness"

[params]
subject_files = ["MISSION.md"]
rubric = "spec-readiness"
rubric_version = "1.0.0"
min_score = 8
max_blockers = 0
requires_human_approval = true
"""


@pytest.fixture
def attached_with_dor(project, corporate_source):
    """A project on a profile that enforces a Definition of Ready."""
    (corporate_source / "rubrics").mkdir()
    (corporate_source / "rubrics" / "spec-readiness-1.0.0.toml").write_text(RUBRIC)
    (corporate_source / "rules" / "DOR-001.toml").write_text(DOR_RULE)
    (corporate_source / "profiles" / "academy-spells-ready.toml").write_text(
        'name = "academy-spells-ready"\n'
        'description = "with a DoR"\n'
        'rules = ["DOR-001", "ARCH-001"]\n'
    )
    git("add", "-A", cwd=corporate_source)
    git("commit", "-q", "-m", "v0.2.0", cwd=corporate_source)
    git("tag", "v0.2.0", cwd=corporate_source)

    (project / "MISSION.md").write_text("# Mission\n\nAdd a frost ward.\n")
    result = subprocess.run(
        [GOLDEN_THREAD_BIN, "-C", str(project), "init",
         "--source", str(corporate_source), "--ref", "v0.2.0",
         "--profile", "academy-spells-ready"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    return project
