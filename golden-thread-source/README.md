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

`academy-spells-ready` is `academy-spells` with the Academy's Definition of
Ready in front of it. Adopting a DoR is therefore a policy change published
under a new tag, and a team adopts it by moving the ref they pin -- no version
of the CLI changes.

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

    golden-thread init --source <this-repo> --ref v0.2.0 \
        --profile academy-spells-ready
