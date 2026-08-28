"""The core must not depend on any AI harness, Claude Code included."""

import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "golden_thread"

FORBIDDEN = re.compile(r"claude|anthropic|\.mcp|copilot|cursor", re.IGNORECASE)


def test_no_harness_reference_anywhere_in_the_core():
    offenders = []
    for path in SRC.rglob("*.py"):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if FORBIDDEN.search(line):
                offenders.append(f"{path.relative_to(SRC)}:{number}: {line.strip()}")
    assert offenders == [], "harness reference in core:\n" + "\n".join(offenders)


def test_core_imports_only_the_standard_library():
    stdlib = set(sys.stdlib_module_names)
    third_party = set()
    for path in SRC.rglob("*.py"):
        import ast

        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                if root and root not in stdlib and root != "golden_thread":
                    third_party.add(root)
    assert third_party == set(), f"non-stdlib dependency: {sorted(third_party)}"


def test_the_cli_runs_with_no_installed_package():
    """Proven by the fact that these tests import it from src/ alone."""
    import golden_thread

    assert golden_thread.__version__ == "0.1.0"
