"""A real Python import graph, built with the stdlib ast module.

This is what makes ARCH-001 an architecture rule rather than a grep. In
particular it resolves relative imports to absolute module paths, so

    from ..elements import fire

is seen for what it is: a dependency on spells.elements.fire.
"""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportEdge:
    source_module: str
    target_module: str
    file: str
    line: int


@dataclass(frozen=True)
class ModuleFile:
    module: str
    path: Path
    is_package: bool


def index_modules(source_root: Path) -> list[ModuleFile]:
    """Map every .py file under source_root to its dotted module path."""
    modules: list[ModuleFile] = []
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(source_root)
        parts = list(relative.parts)
        is_package = parts[-1] == "__init__.py"
        if is_package:
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][: -len(".py")]
        if not parts:
            continue
        modules.append(
            ModuleFile(module=".".join(parts), path=path, is_package=is_package)
        )
    return modules


def resolve_relative(current: str, is_package: bool, level: int, module: str | None) -> str | None:
    """Turn a relative import into an absolute module path.

    `level` is the number of leading dots. Level 1 means the package containing
    the importing module (or the package itself, when the importer is an
    __init__.py).
    """
    parts = current.split(".")
    if not is_package:
        parts = parts[:-1]
    climb = level - 1
    if climb > len(parts):
        return None
    if climb:
        parts = parts[: len(parts) - climb]
    if module:
        parts = parts + module.split(".")
    if not parts:
        return None
    return ".".join(parts)


def _candidates(node: ast.AST, current: ModuleFile) -> list[tuple[str, str, int]]:
    """Yield (base, attribute, line) pairs a node may depend on.

    For `from a.b import c` we cannot tell from syntax alone whether `c` is a
    submodule or a symbol. We return both so the caller can decide using the
    module index, which is authoritative.
    """
    out: list[tuple[str, str, int]] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            out.append((alias.name, "", node.lineno))
    elif isinstance(node, ast.ImportFrom):
        if node.level:
            base = resolve_relative(
                current.module, current.is_package, node.level, node.module
            )
        else:
            base = node.module
        if base:
            for alias in node.names:
                out.append((base, alias.name, node.lineno))
    return out


def build_edges(source_root: Path, modules: list[ModuleFile]) -> list[ImportEdge]:
    """Extract every import edge, keeping only those internal to the project."""
    known = {m.module for m in modules}
    # Packages that exist only as directories still count as internal targets.
    packages = {
        ".".join(m.module.split(".")[:i])
        for m in modules
        for i in range(1, len(m.module.split(".")))
    }
    internal = known | packages

    edges: list[ImportEdge] = []
    for module_file in modules:
        tree = ast.parse(
            module_file.path.read_text(encoding="utf-8"),
            filename=str(module_file.path),
        )
        for node in ast.walk(tree):
            for base, attribute, line in _candidates(node, module_file):
                target = _pick_target(base, attribute, internal)
                if target is None:
                    continue
                edges.append(
                    ImportEdge(
                        source_module=module_file.module,
                        target_module=target,
                        file=str(module_file.path.relative_to(source_root)),
                        line=line,
                    )
                )
    return edges


def _pick_target(base: str, attribute: str, internal: set[str]) -> str | None:
    """Resolve `from base import attribute` against what actually exists."""
    if attribute:
        qualified = f"{base}.{attribute}"
        if qualified in internal:
            return qualified
    if base in internal:
        return base
    return None
