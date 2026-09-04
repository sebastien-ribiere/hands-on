import subprocess
import sys
from pathlib import Path

import pytest

from golden_thread_testkit import (  # noqa: F401
    assessment,
    git,
    publish_dod,
    publish_dor,
    rule,
)

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REPO = Path(__file__).resolve().parents[2]


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
def dor_source(corporate_source):
    """A corporate source whose v0.2.0 publishes a Definition of Ready."""
    return publish_dor(corporate_source)


@pytest.fixture
def mission(spellbook):
    """A mission document for the readiness requirement to be about."""
    path = spellbook / "MISSION.md"
    path.write_text("# Mission: frost ward\n\nAdd a frost ward.\n")
    return path


@pytest.fixture
def spellbook(tmp_path):
    """A compliant consumer project."""
    root = tmp_path / "project"
    spells = root / "src" / "spells"
    for package in ("elements", "protection", "offense"):
        (spells / package).mkdir(parents=True)
        (spells / package / "__init__.py").write_text("")
    (spells / "__init__.py").write_text("")
    (spells / "elements" / "air.py").write_text("def gust():\n    return 'air'\n")
    (spells / "elements" / "water.py").write_text("def mist():\n    return 'water'\n")
    (spells / "elements" / "fire.py").write_text("def scorch(t):\n    return t\n")
    (spells / "protection" / "shield.py").write_text(
        "from spells.elements.air import gust\n\n\ndef cast():\n    return gust()\n"
    )
    (spells / "protection" / "ward.py").write_text(
        "from ..elements import water\n\n\ndef cast():\n    return water.mist()\n"
    )
    (spells / "offense" / "flame_lance.py").write_text(
        "from spells.elements import fire\n\n\ndef cast():\n    return fire.scorch('x')\n"
    )
    return root


@pytest.fixture
def cli(monkeypatch):
    """Run the CLI in-process and capture its exit code."""
    from golden_thread.cli import main

    return main
