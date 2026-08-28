# Golden Thread — Spike 1

A golden path an organisation can distribute, version, and verify.

Spike 1 is the smallest vertical slice that proves the idea end to end: a
project attaches itself to a versioned Golden Thread, knows which version and
profile it is on, runs a real architecture rule, and goes **OFF PATH** when it
breaks that rule.

No workflow engine. No AI agent. No CI. No server. Python standard library only.

## The rule under test

    ARCH-001
    Protection spells may depend on the Air and Water elements.
    They may not depend on Fire.

This is a genuine dependency rule, not a string match. It is checked against the
project's real import graph, built with Python's `ast` module — relative imports
included. `demo-spellbook/src/spells/offense/flame_lance.py` depends on Fire and
stays compliant, because the rule is scoped to the protection layer.

## Layout

    golden-thread-source/    corporate source of authority — POLICY only, versioned by Git tag
      golden-thread.toml       catalog: schema version, default profile
      profiles/                which rules a profile enforces
      rules/ARCH-001.toml      the declarative rule

    golden-thread-cli/       the tool — ENGINE only, stdlib Python, no harness dependency
      src/golden_thread/
        cli.py                 init / status / verify
        manifest.py            the project manifest (lockfile semantics)
        source.py              Git clone and commit resolution
        policy.py              reading the corporate policy
        checks/importgraph.py  the real import graph
        checks/layered_dependencies.py   the check engine
      tests/

    demo-spellbook/          a consumer project
      golden-thread.json       the manifest: minimal, 5 fields
      .golden-thread/          disposable cache, rebuildable from the manifest

    demo/                    the demonstration

Policy and engine are separate on purpose. The corporate repository ships rules
as data, so a Git tag pins the *policy* a team is held to, independently of the
tool version they run.

## Reproducing the demonstration

Everything at once:

    ./demo/run-demo.sh

Or step by step, from the repository root:

    # 0. publish the corporate Golden Thread as a tagged Git repository
    ./demo/publish-source.sh v0.1.0

    # 1. attach the project
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook \
        init --source "$PWD/.demo/golden-thread-source" --ref v0.1.0

    # 2. the project knows its version and profile; nothing verified yet
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status
    #    Architecture  UNKNOWN
    #    PATH STATUS   INCOMPLETE

    # 3. run the architecture rule
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PASS   ARCH-001
    #    PATH STATUS   ON PATH                                  exit 0

    # 4. break ARCH-001: a protection spell reaches into Fire
    printf '\nfrom ..elements import fire\n' \
        >> demo-spellbook/src/spells/protection/ward.py

    # 5. the deviation is detected and located
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   ARCH-001
    #      spells/protection/ward.py:18
    #      spells.protection.ward -> spells.elements.fire
    #    PATH STATUS   OFF PATH                                 exit 1

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status
    #    PATH STATUS   OFF PATH                                 exit 1

    # 6. remove the deviation and return to a compliant state
    git checkout demo-spellbook/src/spells/protection/ward.py
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PATH STATUS   ON PATH                                  exit 0

`golden-thread` is also installable as a normal console script:

    pip install -e golden-thread-cli && golden-thread --help

## Tests

    python3 -m pytest golden-thread-cli/tests -q

## OFF PATH is a signal, not a gate

`verify` exits non-zero and says so plainly, but nothing here blocks a commit,
a build, or a developer. Leaving the golden path stays possible; what Golden
Thread guarantees is that the deviation is explicit rather than silent.

## Exit codes

    0   ON PATH, or INCOMPLETE (nothing verified yet)
    1   OFF PATH
    2   the command itself could not run
