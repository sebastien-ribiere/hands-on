"""The import graph is where a fake check would hide. These tests pin it down."""

from pathlib import Path

from golden_thread.checks.importgraph import (
    build_edges,
    index_modules,
    resolve_relative,
)


def _write(root: Path, relative: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def test_module_paths_are_dotted_and_packages_lose_init(tmp_path):
    _write(tmp_path, "spells/__init__.py", "")
    _write(tmp_path, "spells/protection/shield.py", "")
    modules = {m.module: m.is_package for m in index_modules(tmp_path)}
    assert modules == {"spells": True, "spells.protection.shield": False}


def test_resolve_relative_from_module_walks_up_from_its_package():
    # spells/protection/ward.py doing `from ..elements import fire`
    assert (
        resolve_relative("spells.protection.ward", False, 2, "elements")
        == "spells.elements"
    )


def test_resolve_relative_from_package_starts_at_the_package_itself():
    # spells/protection/__init__.py doing `from .shield import cast`
    assert (
        resolve_relative("spells.protection", True, 1, "shield")
        == "spells.protection.shield"
    )


def test_resolve_relative_beyond_the_root_is_rejected():
    assert resolve_relative("spells", False, 4, "x") is None


def test_from_package_import_submodule_is_seen_as_the_submodule(tmp_path):
    """`from spells.elements import fire` is a dependency on ...elements.fire.

    Recording only `spells.elements` would let every violation through.
    """
    _write(tmp_path, "spells/__init__.py", "")
    _write(tmp_path, "spells/elements/__init__.py", "")
    _write(tmp_path, "spells/elements/fire.py", "")
    _write(tmp_path, "spells/protection/ward.py", "from spells.elements import fire\n")

    edges = build_edges(tmp_path, index_modules(tmp_path))
    targets = {e.target_module for e in edges if e.source_module.endswith("ward")}
    assert "spells.elements.fire" in targets


def test_from_module_import_symbol_is_seen_as_the_module(tmp_path):
    """`from spells.elements.air import gust` depends on the module, not `...air.gust`."""
    _write(tmp_path, "spells/__init__.py", "")
    _write(tmp_path, "spells/elements/air.py", "def gust():\n    pass\n")
    _write(tmp_path, "spells/protection/shield.py",
           "from spells.elements.air import gust\n")

    edges = build_edges(tmp_path, index_modules(tmp_path))
    targets = {e.target_module for e in edges if e.source_module.endswith("shield")}
    assert targets == {"spells.elements.air"}


def test_external_imports_are_not_tracked(tmp_path):
    """Only project-internal edges are policed; stdlib is not the rule's business."""
    _write(tmp_path, "spells/__init__.py", "")
    _write(tmp_path, "spells/protection/shield.py", "import os\nimport json\n")

    assert build_edges(tmp_path, index_modules(tmp_path)) == []


def test_edges_carry_the_real_line_number(tmp_path):
    _write(tmp_path, "spells/__init__.py", "")
    _write(tmp_path, "spells/elements/fire.py", "")
    _write(tmp_path, "spells/protection/ward.py",
           '"""doc."""\n\nimport os\n\nfrom spells.elements import fire\n')

    edges = build_edges(tmp_path, index_modules(tmp_path))
    assert [(e.target_module, e.line) for e in edges] == [("spells.elements.fire", 5)]
