# Golden Thread

A golden path an organisation can distribute, version, and verify.

**Spike 1** proved the vertical slice: a project attaches itself to a versioned
Golden Thread, knows which version and profile it is on, runs a real
architecture rule, and goes **OFF PATH** when it breaks it.

**Spike 2** makes every verdict accountable. There is no `architecture: true`
anywhere. A status is only ever reported together with the *evidence* it came
from — and evidence that no longer describes the code is reported as **STALE**
rather than quietly reused.

No workflow engine. No AI agent. No CI. No server. Python standard library only.

## The rule under test

    ARCH-001
    Protection spells may depend on the Air and Water elements.
    They may not depend on Fire.

This is a genuine dependency rule, not a string match. It is checked against the
project's real import graph, built with Python's `ast` module — relative imports
included. `demo-spellbook/src/spells/offense/flame_lance.py` depends on Fire and
stays compliant, because the rule is scoped to the protection layer.

## Evidence

One record per requirement, answering five questions and nothing more:

| Field | Question | Example |
|---|---|---|
| `requirement` | which requirement? | `ARCH-001` |
| `subject` | verified on what? | `src/`, 10 files, `sha256:cdd324e7312c…` |
| `producer` | by which producer? | `golden-thread 0.2.0` |
| `method` | with which method? | `layered_dependencies`, profile `academy-spells`, policy `v0.1.0 @ 651f644a18bf` |
| `result` | with which result? | `PASS`, or `FAIL` with the exact violations |
| `timestamp` | when? | `2026-08-28T07:53:51+00:00` |

Requirement and rule are one-to-one: a rule is how a requirement is made
checkable. There is no confidence score, no signature, no central store and no
evidence taxonomy.

Records live in `.golden-thread/evidence.json`, which holds the **latest**
record per requirement. It is a current-state file, not an audit journal, and
it is disposable: `verify` rebuilds it.

### The subject, and why old evidence cannot be reused

The invalidation mechanism is one thing only:

> **a `sha256` digest over the sorted `(relative path, sha256(content))` pairs
> of the exact files the check engine read.**

`status` re-identifies the subject and compares. Equal, and the record still
speaks about the code in front of us. Different, and it does not — so it is
reported as STALE, never as a verdict.

The digest covers the three ways a subject can change (content edited, file
added, file removed). It deliberately covers *nothing else*: editing a README
does not invalidate an architecture verdict, because false invalidation is how
a staleness mechanism gets ignored.

A Git revision is recorded when one is available, but it is **descriptive
only**. A worktree with uncommitted work is not identified by its HEAD, and a
project is not always its own repository.

A record is also stale when the **method** changed — a different Golden Thread
revision, or a different profile. Evidence produced under `v0.1.0` says nothing
about `v0.2.0`'s rules.

## Path status

| Status | Meaning | Exit |
|---|---|---|
| `INCOMPLETE` | nothing has been verified yet | 0 |
| `ON PATH` | every requirement has current, passing evidence | 0 |
| `OFF PATH` | a requirement failed, on evidence that still applies | 1 |
| `STALE` | evidence exists but no longer describes this code or this policy | 3 |

Precedence, most definite fact first: a confirmed failure outranks staleness;
unknown outranks a comfortable assumption. `ON PATH` is only claimed when every
requirement is both current and passing.

`OFF PATH` is a signal, not a gate. `verify` exits non-zero and says so plainly,
but nothing here blocks a commit, a build, or a developer. Leaving the golden
path stays possible; what Golden Thread guarantees is that the deviation is
explicit rather than silent. `STALE` is deliberately *not* exit 1: "a rule
failed" and "we do not know" are different facts, and conflating them is the
kind of lie this spike exists to remove.

## Layout

    golden-thread-source/    corporate source of authority — POLICY only, versioned by Git tag
      golden-thread.toml       catalog: schema version, default profile
      profiles/                which rules a profile enforces
      rules/ARCH-001.toml      the declarative rule

    golden-thread-cli/       the tool — ENGINE only, stdlib Python, no harness dependency
      src/golden_thread/
        cli.py                 init / status / verify, human and --json output
        manifest.py            the project manifest (lockfile semantics)
        source.py              Git clone and commit resolution
        policy.py              reading the corporate policy
        subject.py             what a requirement was verified on, by content digest
        evidence.py            the evidence record, and whether it still applies
        verify.py              producing evidence
        status.py              reading evidence, and the path status it implies
        state.py               where records are kept
        report.py              the machine-readable report
        checks/importgraph.py  the real import graph
        checks/layered_dependencies.py   the check engine
      tests/

    demo-spellbook/          a consumer project
      golden-thread.json       the manifest: minimal, 5 fields
      .golden-thread/          disposable: policy cache + recorded evidence

    demo/                    the demonstration

Policy and engine are separate on purpose. The corporate repository ships rules
as data, so a Git tag pins the *policy* a team is held to, independently of the
tool version they run.

`verify` produces evidence; `status` only reads it. Re-identifying a subject is
not producing evidence: `status` runs no check, it establishes whether what was
recorded still applies.

## Reproducing the demonstration

Everything at once — attach, verify, invalidate, repair:

    ./demo/run-demo.sh

Or step by step, from the repository root:

    # 0. publish the corporate Golden Thread as a tagged Git repository
    ./demo/publish-source.sh v0.1.0

    # 1. attach the project
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook \
        init --source "$PWD/.demo/golden-thread-source" --ref v0.1.0

    # 2. nothing verified yet — and that is said, not assumed
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status
    #    UNKNOWN ARCH-001  Protection spells must not depend on Fire
    #           never verified
    #    PATH STATUS   INCOMPLETE                               exit 0

    # 3. run the architecture rule; evidence is produced
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PASS   ARCH-001  Protection spells must not depend on Fire
    #           subject   src/ - 10 file(s) sha256:cdd324e7312c
    #           method    layered_dependencies - academy-spells - policy v0.1.0 @ 651f644a18bf
    #           producer  golden-thread 0.2.0
    #    PATH STATUS   ON PATH                                  exit 0

    cat demo-spellbook/.golden-thread/evidence.json

    # 4. change a verified file without re-verifying
    printf '\n# a later thought\n' >> demo-spellbook/src/spells/protection/shield.py

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status
    #    STALE  ARCH-001
    #           recorded PASS no longer applies:
    #             - the code changed: 10 file(s) cdd324e7312c -> 10 file(s) 27d737e001f1
    #    PATH STATUS   STALE                                    exit 3

    # 5. break ARCH-001: a protection spell reaches into Fire
    printf '\nfrom ..elements import fire\n' \
        >> demo-spellbook/src/spells/protection/ward.py

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   ARCH-001
    #           spells/protection/ward.py:18
    #           spells.protection.ward -> spells.elements.fire
    #    PATH STATUS   OFF PATH                                 exit 1

    # 6. repair the code — the recorded FAIL is not silently kept either
    git checkout demo-spellbook/src/spells/protection/ward.py
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status
    #    PATH STATUS   STALE                                    exit 3

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PATH STATUS   ON PATH                                  exit 0

    # 7. the same report, machine-readable
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook status --json

    git checkout demo-spellbook/src/spells/protection/shield.py

`golden-thread` is also installable as a normal console script:

    pip install -e golden-thread-cli && golden-thread --help

## The machine-readable report

`--json` on `status` or `verify` prints one document to stdout, carrying the
same evidence the human output describes:

    {
      "reportVersion": 1,
      "command": "status",
      "pathStatus": "STALE",
      "exitCode": 3,
      "goldenThread": { "source": "...", "ref": "v0.1.0", "revision": "651f…", "profile": "academy-spells" },
      "requirements": [
        {
          "requirement": "ARCH-001",
          "reportedStatus": "STALE",
          "freshness": {
            "state": "STALE",
            "reasons": ["the code changed: 10 file(s) cdd324e7312c -> 10 file(s) 27d737e001f1"],
            "currentSubjectDigest": "sha256:27d737e001f1…"
          },
          "evidence": { "requirement": "...", "subject": {...}, "producer": {...}, "method": {...}, "result": {...} }
        }
      ]
    }

`reportedStatus` is what may be believed today. The recorded `result.status`
is still there, but as history — never as the answer.

## Tests

    python3 -m pytest golden-thread-cli/tests -q

## Exit codes

    0   ON PATH, or INCOMPLETE (nothing verified yet)
    1   OFF PATH
    2   the command itself could not run
    3   STALE: evidence exists but no longer describes this project
