"""Check engine: layered_dependencies.

Given layers declared in the corporate policy, verify the project's real import
graph respects them. Precedence, in order:

  1. a dependency inside the layer's own subtree is always allowed;
  2. a dependency matching `deny` is a violation      -> reason "denied";
  3. a dependency matching `allow` is permitted;
  4. anything else internal is a violation            -> reason "not-allowed".

Deny wins over allow, so an explicitly forbidden dependency reports as such
even if a broader allow entry would have covered it.
"""

from pathlib import Path

from .. import subject as subject_mod
from ..errors import GoldenThreadError
from ..results import ERROR, FAIL, PASS, RuleResult, Violation
from ..subject import Subject
from .importgraph import build_edges, index_modules

NAME = "layered_dependencies"


def _matches(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def _parse_layers(params: dict) -> list[dict]:
    layers = params.get("layers")
    if not layers:
        raise GoldenThreadError("rule params declare no 'layers'")
    for layer in layers:
        if not layer.get("match"):
            raise GoldenThreadError(
                f"layer {layer.get('name', '?')!r} declares no 'match'"
            )
    return layers


def _source_root(rule, project: Path) -> Path:
    return project / rule.params.get("source_root", "src")


def subject(rule, project: Path) -> Subject:
    """The exact files this engine reads, identified by content.

    Never raises for a missing source root: an absent subject is a fact
    about the subject, and the digest still moves the moment something
    appears.
    """
    root = _source_root(rule, project)
    modules = index_modules(root) if root.is_dir() else []
    return subject_mod.identify(project, root, [m.path for m in modules])


def run(rule, project: Path) -> RuleResult:
    params = rule.params
    source_root = _source_root(rule, project)
    scanned = subject(rule, project)

    try:
        layers = _parse_layers(params)
        if not source_root.is_dir():
            raise GoldenThreadError(
                f"source root {params.get('source_root', 'src')!r} does not exist "
                f"in this project (looked in {source_root})"
            )

        modules = index_modules(source_root)
        if not modules:
            # An empty scan is not a pass. It means the rule never ran.
            raise GoldenThreadError(f"no Python modules found under {source_root}")

        edges = build_edges(source_root, modules)
    except GoldenThreadError as exc:
        return RuleResult(status=ERROR, subject=scanned, error=str(exc))
    except SyntaxError as exc:
        return RuleResult(
            status=ERROR,
            subject=scanned,
            error=f"could not parse {exc.filename}: {exc.msg} (line {exc.lineno})",
        )

    violations: list[Violation] = []
    for layer in layers:
        match = layer["match"]
        allow = layer.get("allow", [])
        deny = layer.get("deny", [])

        for edge in edges:
            if not _matches(edge.source_module, match):
                continue
            target = edge.target_module
            if _matches(target, match):
                continue  # intra-layer dependencies are the layer's own business

            denied = next((d for d in deny if _matches(target, d)), None)
            if denied:
                violations.append(
                    Violation(
                        file=edge.file,
                        line=edge.line,
                        source_module=edge.source_module,
                        target_module=target,
                        reason=f"layer '{layer.get('name', match)}' must not depend on {denied}",
                    )
                )
                continue

            if any(_matches(target, a) for a in allow):
                continue

            violations.append(
                Violation(
                    file=edge.file,
                    line=edge.line,
                    source_module=edge.source_module,
                    target_module=target,
                    reason=f"layer '{layer.get('name', match)}' may only depend on "
                    f"{', '.join(allow) or 'itself'}",
                )
            )

    violations.sort(key=lambda v: (v.file, v.line))
    return RuleResult(
        status=FAIL if violations else PASS,
        subject=scanned,
        violations=violations,
    )
