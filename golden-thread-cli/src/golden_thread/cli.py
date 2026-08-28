"""The golden-thread command line.

Exit codes:
  0  ON PATH, or INCOMPLETE (nothing verified yet)
  1  OFF PATH: a rule failed or could not run
  2  the command itself could not run
"""

import argparse
import sys
from pathlib import Path

from . import manifest as manifest_mod
from . import policy, source, state, status as status_mod, verify
from .errors import GoldenThreadError
from .paths import WORK_DIR_NAME
from .results import ERROR, PASS

LABEL_WIDTH = 14


def _line(label: str, value: str) -> str:
    return f"{label.ljust(LABEL_WIDTH)}{value}"


def _ensure_gitignored(project: Path) -> None:
    """Keep the cache and recorded evidence out of the consumer's history."""
    entry = f"{WORK_DIR_NAME}/"
    gitignore = project / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if entry in existing.split():
        return
    prefix = "" if existing.endswith("\n") or not existing else "\n"
    gitignore.write_text(
        f"{existing}{prefix}# Golden Thread cache and recorded evidence\n{entry}\n",
        encoding="utf-8",
    )


def cmd_init(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    if not project.is_dir():
        raise GoldenThreadError(f"project directory does not exist: {project}")

    dest = project / WORK_DIR_NAME / "source"
    revision = source.clone_at_ref(args.source, args.ref, dest)
    profile_name = args.profile or policy.default_profile_name(dest)
    # Fail at init, not at first verify, if the profile does not exist.
    profile = policy.load_profile(dest, profile_name)

    written = manifest_mod.write(
        project,
        manifest_mod.Manifest(
            source=args.source,
            ref=args.ref,
            revision=revision,
            profile=profile.name,
        ),
    )
    _ensure_gitignored(project)

    print("Golden Thread attached")
    print(_line("Source", args.source))
    print(_line("Version", args.ref))
    print(_line("Revision", revision))
    print(_line("Profile", profile.name))
    print(_line("Rules", ", ".join(r.id for r in profile.rules) or "none"))
    print()
    print(f"Manifest      {written.relative_to(project)}")
    print("Next          golden-thread verify")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    manifest = manifest_mod.read(project)
    current = status_mod.compute(project, manifest)

    print("Golden Thread")
    print(_line("Version", manifest.ref))
    print(_line("Revision", manifest.short_revision))
    print(_line("Profile", manifest.profile))
    print()
    print(_line("Architecture", current.architecture))
    print(_line("PATH STATUS", current.path_status))

    if current.path_status == status_mod.INCOMPLETE:
        print()
        print("Nothing verified yet. Run: golden-thread verify")
        return 0

    print()
    print(f"Last verified {current.verified_at}")
    if current.failing_rules:
        print(f"Failing rules {', '.join(current.failing_rules)}")
        print("Run 'golden-thread verify' for details.")
        return 1
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    manifest = manifest_mod.read(project)
    result = verify.run(project, manifest)
    state.save(project, result)

    print("Golden Thread verify")
    print(_line("Version", manifest.ref))
    print(_line("Revision", manifest.short_revision))
    print(_line("Profile", result.profile))
    print()

    for rule in result.rules:
        print(f"{rule.status.ljust(6)} {rule.rule_id}  {rule.title}")
        if rule.status == ERROR:
            print(f"       could not run: {rule.error}")
        for violation in rule.violations:
            print(f"       {violation.file}:{violation.line}")
            print(
                f"         {violation.source_module} -> {violation.target_module}"
            )
            print(f"         {violation.reason}")
        print()

    if result.status == PASS:
        print(f"PATH STATUS   {status_mod.ON_PATH}")
        return 0

    total = sum(len(r.violations) for r in result.rules)
    print(f"PATH STATUS   {status_mod.OFF_PATH}")
    print()
    print(
        f"{total} violation(s). This is a signal, not a block: you may stay "
        "off path deliberately,"
    )
    print("but the deviation is now explicit.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="golden-thread",
        description="Attach a project to a versioned Golden Thread and verify it.",
    )
    parser.add_argument(
        "-C",
        "--project",
        default=".",
        help="project directory (default: current directory)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="attach this project to a Golden Thread")
    init.add_argument("--source", required=True, help="Git repository of the Golden Thread")
    init.add_argument("--ref", required=True, help="tag or branch to pin, e.g. v0.1.0")
    init.add_argument("--profile", help="profile to use (default: the source's own)")
    init.set_defaults(func=cmd_init)

    status = subparsers.add_parser("status", help="show version, profile and path status")
    status.set_defaults(func=cmd_status)

    verify_cmd = subparsers.add_parser("verify", help="run the profile's rules")
    verify_cmd.set_defaults(func=cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GoldenThreadError as exc:
        print(f"golden-thread: {exc}", file=sys.stderr)
        return 2
