# Golden Thread - corporate source

Source of authority for the Golden Thread golden path.

- `golden-thread.toml` - catalog: schema version, default profile
- `profiles/<name>.toml` - which rules a profile enforces
- `rules/<id>.toml` - declarative rule definitions

This repository contains **policy only**. The verification engine lives in the
`golden-thread` CLI. That split is what makes a Git tag meaningful: consumers
pin a version of the policy, not a version of the tool.

Consumed by projects with:

    golden-thread init --source <this-repo> --ref v0.1.0
