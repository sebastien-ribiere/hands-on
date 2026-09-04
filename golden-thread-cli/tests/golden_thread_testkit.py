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


DOD_RULES = {
    "TEST-001": """
id = "TEST-001"
title = "The test suite passes"
check = "external_command"

[params]
command = ["python3", "-c", "import sys; sys.exit(0)"]
subject_globs = ["src/**/*.py"]
""",
    "SEC-001": """
id = "SEC-001"
title = "No known security defect at MEDIUM or above"
check = "security_scan"

[params]
format = "bandit"
command = ["bandit", "-r", "src", "-f", "json", "-q"]
subject_root = "src"
subject_globs = ["**/*.py"]
fail_on_severity = "MEDIUM"
min_confidence = "MEDIUM"
""",
    "DOC-001": """
id = "DOC-001"
title = "The documentation describes the code that ships"
check = "doc_stamp"

[params]
document = "docs/ARCHITECTURE.md"
describes = "src"
describes_globs = ["**/*.py"]
""",
    "COOKIE-001": """
id = "COOKIE-001"
title = "Cookies were prepared and shared with the team"
check = "human_attestation"

[params]
statement = "Cookies have been prepared and shared with the team."
subject_root = "src"
subject_globs = ["**/*.py"]
""",
}


def publish_dod(source_root, rules, profile="academy-spells-done", tag="v0.3.0"):
    """Add a Definition of Done to an existing corporate source, and tag it.

    `rules` is the profile's requirement list, in order. Ids already published
    by the source -- ARCH-001 -- are listed rather than rewritten, so a test can
    mix new requirements with the ones that were always there; ids this helper
    knows are written out. A test that does not need bandit simply leaves
    SEC-001 out of the list.
    """
    for rule_id in rules:
        if rule_id in DOD_RULES:
            (source_root / "rules" / f"{rule_id}.toml").write_text(DOD_RULES[rule_id])
    listed = ", ".join(f'"{rule_id}"' for rule_id in rules)
    (source_root / "profiles" / f"{profile}.toml").write_text(
        f'name = "{profile}"\ndescription = "with a DoD"\nrules = [{listed}]\n'
    )
    git("add", "-A", cwd=source_root)
    git("commit", "-q", "-m", tag, cwd=source_root)
    git("tag", tag, cwd=source_root)
    return source_root


def rule(rule_id, check, **params):
    """A Rule object, for testing an engine without a repository around it."""
    from golden_thread.policy import Rule

    return Rule(id=rule_id, title=rule_id, check=check, params=params)


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
