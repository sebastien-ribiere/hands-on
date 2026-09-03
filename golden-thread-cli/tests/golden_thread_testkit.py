"""Helpers shared between conftest and the test modules themselves.

Deliberately not in conftest.py. Both test suites in this repository have a
conftest, so `from conftest import ...` is ambiguous the moment pytest is
pointed at both directories at once -- which is exactly how the full suite is
run. A uniquely named module is unambiguous wherever it is imported from.
"""

import subprocess


def git(*args, cwd):
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
         "-c", "user.name=Test", "-c", "user.email=test@local", *args],
        cwd=str(cwd), check=True, capture_output=True, text=True,
    )


RUBRIC = """
id = "spec-readiness"
version = "1.0.0"
title = "Is this mission ready?"
scale_max = 10
caveat = "An assessment, not a measurement."

[[dimensions]]
id = "problem"
title = "The problem"
points = 4
asks = "Is the problem stated?"

[[dimensions]]
id = "outcome"
title = "An observable outcome"
points = 3
asks = "Could someone tell it was done?"

[[dimensions]]
id = "scope"
title = "A drawn boundary"
points = 3
asks = "Is what is out of scope stated?"
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


def publish_dor(source_root, tag="v0.2.0", rubric_version="1.0.0"):
    """Add a Definition of Ready to an existing corporate source, and tag it.

    Adding a readiness requirement to a golden path is a policy change: a new
    rubric, a new rule and a new profile in the corporate repository, under a
    new tag. Never a code change in the CLI. These tests exercise it that way.
    """
    (source_root / "rubrics").mkdir(exist_ok=True)
    (source_root / "rubrics" / f"spec-readiness-{rubric_version}.toml").write_text(
        RUBRIC.replace('version = "1.0.0"', f'version = "{rubric_version}"')
    )
    (source_root / "rules" / "DOR-001.toml").write_text(
        DOR_RULE.replace(
            'rubric_version = "1.0.0"', f'rubric_version = "{rubric_version}"'
        )
    )
    (source_root / "profiles" / "academy-spells-ready.toml").write_text(
        'name = "academy-spells-ready"\n'
        'description = "with a DoR"\n'
        'rules = ["DOR-001", "ARCH-001"]\n'
    )
    git("add", "-A", cwd=source_root)
    git("commit", "-q", "-m", tag, cwd=source_root)
    git("tag", tag, cwd=source_root)
    return source_root


def assessment(score=9, **overrides):
    """A well-formed assessment against the test rubric (4 + 3 + 3 = 10)."""
    problem = min(4, score)
    outcome = min(3, max(0, score - problem))
    scope = score - problem - outcome
    data = {
        "assessor": "a model, in a test",
        "rubric": "spec-readiness@1.0.0",
        "score": score,
        "dimensions": [
            {"id": "problem", "score": problem, "note": "stated"},
            {"id": "outcome", "score": outcome, "note": "partly"},
            {"id": "scope", "score": scope, "note": "partly"},
        ],
        "facts": ["the mission names a module"],
        "assumptions": ["conventions are followed"],
        "unknowns": ["the exact wording"],
        "unknownUnknowns": ["the taxonomy may have rules we were not told"],
        "blockers": [],
        "decisions": [],
    }
    data.update(overrides)
    return data
