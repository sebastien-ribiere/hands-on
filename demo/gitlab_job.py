"""Read a job out of .gitlab-ci.yml, as GitLab would assemble it.

Used by demo/run-ci-locally.sh so the local run executes the pipeline's own
lines rather than a copy of them that can drift.

What is reproduced here is deliberately the small, stable part of GitLab's
behaviour: `default.image` unless the job overrides it, `default.before_script`
unless the job overrides it, then the job's `script`, all concatenated into one
shell script so a variable set on one line is still set on the next -- which is
how GitLab runs them, and what makes `gt_exit=$?` on one line and
`exit $gt_exit` on another work at all.

`variables` are emitted as shell assignments before the script, the same way
the runner exports them. Everything else in the GitLab schema -- rules, needs,
services, caches, matrices -- is not interpreted, and a job using them is not
one this script can honestly claim to have run.
"""

import argparse
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - a setup problem, not a code path
    raise SystemExit(
        "demo/gitlab_job.py needs PyYAML to read .gitlab-ci.yml.\n"
        "Run: ./demo/install-toolchain.sh\n"
        "\n"
        "This is a dependency of the demo runner only. The golden-thread CLI "
        "is stdlib-only and does not read YAML at all."
    )

UNSUPPORTED = ("services", "parallel", "trigger", "needs", "extends")


def load(path: str, job_name: str) -> tuple[dict, dict]:
    with open(path, encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if job_name not in document:
        raise SystemExit(f"no job {job_name!r} in {path}")
    return document, document[job_name]


def assemble(document: dict, job: dict) -> str:
    default = document.get("default", {})
    lines = ["#!/usr/bin/env bash", "# Assembled from .gitlab-ci.yml. Do not edit."]

    for name, value in (document.get("variables") or {}).items():
        lines.append(f'export {name}="{value}"')
    for name, value in (job.get("variables") or {}).items():
        lines.append(f'export {name}="{value}"')

    for section in ("before_script", "script"):
        block = job.get(section, default.get(section) if section == "before_script" else None)
        if not block:
            continue
        lines.append(f"# --- {section} ---")
        lines.extend(block)

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipeline")
    parser.add_argument("job")
    parser.add_argument("--image", action="store_true")
    parser.add_argument("--script", action="store_true")
    parser.add_argument("--artifacts", action="store_true")
    args = parser.parse_args()

    document, job = load(args.pipeline, args.job)

    used = [key for key in UNSUPPORTED if key in job]
    if used:
        print(
            f"job {args.job!r} uses {', '.join(used)}, which this runner does "
            "not interpret. Running it would be a claim about a pipeline that "
            "was not run.",
            file=sys.stderr,
        )
        return 2

    if args.image:
        print(job.get("image", document.get("default", {}).get("image", "")))
    if args.script:
        print(assemble(document, job), end="")
    if args.artifacts:
        print(" ".join((job.get("artifacts") or {}).get("paths", [])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
