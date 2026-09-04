# Golden Thread - corporate source

Source of authority for the Golden Thread golden path.

- `golden-thread.toml` - catalog: schema version, default profile
- `profiles/<name>.toml` - which rules a profile enforces
- `rules/<id>.toml` - declarative rule definitions
- `rubrics/<id>-<version>.toml` - versioned rubrics an assessment is made against

This repository contains **policy only**. The verification engine lives in the
`golden-thread` CLI. That split is what makes a Git tag meaningful: consumers
pin a version of the policy, not a version of the tool.

## Profiles

    academy-spells         ARCH-001
    academy-spells-ready   DOR-001, ARCH-001
    academy-spells-done    DOR-001, TEST-001, ARCH-001, SEC-001, DOC-001, COOKIE-001

Each is the previous one with more of the contract written down. Adopting one
is a policy change published under a new tag, and a team adopts it by moving
the ref they pin.

There is no separate "Definition of Ready" or "Definition of Done" object in
this schema, and there does not need to be one. A profile is the list of
requirements a team is held to; the DoR and the DoD are that list read at two
moments. What distinguishes them in a report is not a label written here but
what the engines can do: a readiness requirement reports NOT READY, because the
work was never agreed, and everything else reports OFF PATH, because something
in the work is not done.

## Requirements, and what each kind of evidence is worth

    ARCH-001     the project's real import graph
    TEST-001     a command this file names, and its exit code
    SEC-001      bandit, and the severity threshold set in that rule
    DOC-001      a digest stamp inside the documentation
    COOKIE-001   a person's word, and nothing else

The last one is deliberately absurd, and it is load-bearing: every
organisation's Definition of Done contains something no tool can establish, and
a policy language that could only express the checkable would quietly drop
those. Read `rules/COOKIE-001.toml` before removing it.

## Where the CLI ends and this repository begins

Adding a *requirement* is a change here and a new tag. Adding a new *kind* of
check is a change to the CLI, because an engine is code. v0.1.0 and v0.2.0
needed no CLI release at all; v0.3.0 introduced four requirements, two of which
needed engines that did not exist.

That boundary is worth keeping visible rather than blurring: a rule declaring
`check = "security_scan"` is naming something the tool must already know how to
do. It cannot invent one in TOML.

## Rules may name a command, and it is an argv list

`TEST-001` and `SEC-001` declare what to run:

    command = ["python3", "-m", "pytest", "-q", "tests"]

A list, never a string. No shell is involved, so there is nothing to quote,
nothing to expand, and no way for a policy file to smuggle a second command
past a reader. The argv is recorded in the evidence, so what ran appears in the
report rather than only in this repository.

This is the point where adopting a golden path means running its verifications.
That was already true of a `.gitlab-ci.yml` include; it is stated here rather
than left implied.

## Rubrics are versioned twice over

By file name, so publishing a revision is an added file and a one-line change
to the rule that pins it -- both visible in a diff, with the old rubric still
present for anything that cites it. And by the `version` field inside the file,
which is what every assessment records.

That second half is what makes a score auditable. An assessment made under
`spec-readiness@1.0.0` is never silently reinterpreted as a score under
`1.1.0`: it stops applying and says which version it was made under.

A rubric also carries its own `caveat`, printed verbatim by the CLI rather than
paraphrased. The statement that a readiness score is an assessment and not a
measurement is part of the policy, not a disclaimer the tool adds.

Consumed by projects with:

    golden-thread init --source <this-repo> --ref v0.3.0 \
        --profile academy-spells-done
