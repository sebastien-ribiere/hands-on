# Golden Thread

A golden path an organisation can distribute, version, and verify.

**Spike 1** proved the vertical slice: a project attaches itself to a versioned
Golden Thread, knows which version and profile it is on, runs a real
architecture rule, and goes **OFF PATH** when it breaks it.

**Spike 2** makes every verdict accountable. There is no `architecture: true`
anywhere. A status is only ever reported together with the *evidence* it came
from — and evidence that no longer describes the code is reported as **STALE**
rather than quietly reused.

**Spike 3** adds a minimal Claude Code adapter, proving the core is usable
from inside a real Claude Code session without moving any Golden Thread logic
into Claude Code. See [`claude-code-adapter/README.md`](claude-code-adapter/README.md).

**Spike 4** adds a **Definition of Ready** — the first requirement Golden Thread
cannot verify by itself. `DOR-001` is satisfied by two claims made elsewhere: an
assessment produced against a versioned rubric, and a decision made by a person.
Neither is sufficient alone, and the CLI produces neither.

The core is still stdlib-only Python with no dependency on any AI harness. The
assessment arrives from outside it; the rubric is data in the corporate policy.

## The rule under test

    ARCH-001
    Protection spells may depend on the Air and Water elements.
    They may not depend on Fire.

This is a genuine dependency rule, not a string match. It is checked against the
project's real import graph, built with Python's `ast` module — relative imports
included. `demo-spellbook/src/spells/offense/flame_lance.py` depends on Fire and
stays compliant, because the rule is scoped to the protection layer.

## The Definition of Ready

    DOR-001
    A mission is Ready before implementation starts.

Satisfied only when **both** of these hold:

    an assessment scoring >= 8/10 against spec-readiness@1.0.0, with no blockers
      +
    a human attestation recording a person's decision

### The score is an assessment, not a measurement

Two assessors reading the same mission against the same rubric will disagree.
This is not a caveat added by the tool — it is written into the rubric itself,
in `caveat`, and printed verbatim by `golden-thread readiness rubric`.

It was also observed rather than assumed. On the demo's own mission, under
`spec-readiness@1.0.0`, the canned assessment in `demo/assessment-initial.json`
scores **7/10** and a live model session scored the identical document **3/10**,
raising a decision neither the mission nor the canned assessment had noticed
(there is no ice element in `src/spells/elements/`). Same rubric, same text,
different readers, different numbers. That is the normal case.

So a score is never treated as a fact. It is recorded as one named party's
opinion, with the rubric version it was made under attached, and it makes a
mission *eligible for a human decision* — nothing more.

### Neither half can stand in for the other

- **No score satisfies DOR-001 alone**, including 10/10. With
  `requires_human_approval = true`, the engine has no code path that passes on
  an assessment by itself.
- **No approval moves the threshold.** `min_score` lives in the corporate
  policy. A person approving a 7/10 records their approval, and the requirement
  still reports 7 as below 8.
- **A blocker beats any score.** `max_blockers = 0` means one open blocker is
  not ready at 10/10.

### The rubric is versioned twice over

By file name — `rubrics/spec-readiness-1.0.0.toml` — so publishing a revision
is an added file and a one-line rule change, both visible in a diff. And by the
`version` field inside it, which every assessment records as
`spec-readiness@1.0.0`. When a profile later pins `1.1.0`, a recorded
assessment does not get silently reinterpreted under the new rubric: it stops
applying, and says which version it was made under.

### Both claims are tied to the text they were made about

An assessment and an approval each record the subject digest of the mission
document. Edit the mission after approving, and neither claim carries over —
an approval is given to a text, not to a file name. This is the same mechanism
Spike 2 built for code, applied unchanged to a Markdown file.

### The approval boundary, stated honestly

`golden-thread readiness approve` prints the assessment, names the attestor,
and requires a confirmation phrase derived from the subject digest. Without a
terminal it refuses rather than assumes, directing the caller to `--confirm`.

**This makes approval a deliberate act. It does not prove a human performed
it**, and nothing on a developer machine can. What it buys is attribution and
intent: an approval cannot be recorded by accident, cannot be recorded without
naming who is approving, and cannot be replayed against a different text.

The agent side is enforced separately and structurally: the `spec-readiness`
skill never runs an approval, and
`claude-code-adapter/tests/test_adapter_is_isolated.py` parses the shell fences
out of every `SKILL.md` and fails if `approve` appears among the commands a
skill tells an agent to run. Verified live: asked to approve on the user's
explicit authority, the session re-assessed to 9/10 and declined, and no
`human-attestation` was written.

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
| `NOT READY` | a readiness requirement is not satisfied | 4 |
| `STALE` | evidence exists but no longer describes this code or this policy | 3 |

`NOT READY` outranks `OFF PATH`. A readiness requirement is a precondition on
the work itself, and announcing "the code you wrote has an architecture
violation" while the mission was never agreed answers the second question
first. Both requirements are still listed individually — only the headline
changes.

Below that, the original rule stands: a confirmed failure outranks staleness;
unknown outranks a comfortable assumption. `ON PATH` is only claimed when every
requirement is both current and passing.

`NOT READY` is not a gate either. A Definition of Ready that blocked would be a
different tool: nothing here stops a developer writing code against an
un-agreed mission. What it stops is that being *implicit*.

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
      rules/ARCH-001.toml      the declarative architecture rule
      rules/DOR-001.toml       the Definition of Ready: rubric pinned, thresholds set
      rubrics/spec-readiness-1.0.0.toml   the versioned rubric, with its own caveat

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
        attestation.py         claims the CLI received rather than produced
        rubric.py              loading the versioned rubric from the pinned policy
        readiness.py           publish the rubric, validate an assessment, witness a decision
        checks/importgraph.py  the real import graph
        checks/layered_dependencies.py   the architecture check engine
        checks/spec_readiness.py         the readiness engine — reads claims, runs no check
      tests/

    demo-spellbook/          a consumer project
      golden-thread.json       the manifest: minimal, 5 fields
      MISSION.md               what DOR-001 is about, digested by content
      .golden-thread/          disposable: policy cache, evidence, attestations
      .claude/settings.json     registers the Claude Code adapter's hooks
      .claude/skills/          symlink to the adapter's skills

    claude-code-adapter/     Spike 3 — harness-specific glue, isolated from the core
      hooks/session_start.py   shows Golden Thread context at session start
      hooks/pre_tool_use.py    signals OFF PATH/STALE/NOT READY before Edit/Write, never blocks
      skills/spec-readiness/   Spike 4 — the skill that assesses, and may never approve
      lib/                     the only code that shells out to `golden-thread`
      tests/

    demo/                    the demonstration

Policy and engine are separate on purpose. The corporate repository ships rules
as data, so a Git tag pins the *policy* a team is held to, independently of the
tool version they run.

`verify` produces evidence; `status` only reads it. Re-identifying a subject is
not producing evidence: `status` runs no check, it establishes whether what was
recorded still applies.

## Reproducing the demonstration

Two demonstrations. Spike 1–2 — attach, verify, invalidate, repair:

    ./demo/run-demo.sh

Spike 4 — the Definition of Ready, from NOT READY to READY:

    ./demo/run-dor-demo.sh

Or step by step, from the repository root:

    # 0. publish the corporate Golden Thread as a tagged Git repository.
    #    v0.1.0 is the golden path before the DoR; v0.2.0 adds it.
    ./demo/publish-source.sh

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

### The Definition of Ready, step by step

    # 1. attach to the profile that enforces a DoR
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook init \
        --source "$PWD/.demo/golden-thread-source" --ref v0.2.0 \
        --profile academy-spells-ready

    # 2. nothing assessed, nobody asked
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   DOR-001  A mission is Ready before implementation starts
    #           - no readiness assessment on record
    #           - no human approval on record. A readiness score never approves itself.
    #    PATH STATUS   NOT READY                                exit 4

    # 3. the rubric is policy, published by the golden path
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook readiness rubric

    # 4. an assessment arrives — from the skill, or canned for reproducibility
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook \
        readiness assess --input demo/assessment-initial.json
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   DOR-001
    #           - assessed at 7/10, below the 8 this profile requires
    #           - 2 decision(s) still awaiting a human answer
    #    PATH STATUS   NOT READY                                exit 4

    # 5. the developer answers the decisions in the mission itself
    cp demo/mission-clarified.md demo-spellbook/MISSION.md

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   DOR-001
    #           - the assessment was made about a different version of the mission
    #    PATH STATUS   NOT READY                                exit 4

    # 6. re-assess: 9/10, no blockers, no open decisions — and still not ready
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook \
        readiness assess --input demo/assessment-clarified.json
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   DOR-001
    #           - assessed at 9/10 against spec-readiness@1.0.0, at or above the 8 ...
    #           - no human approval on record.
    #    PATH STATUS   NOT READY                                exit 4

    # 7. a human decides. Interactive: it prints what is being decided and
    #    asks for a phrase tied to this exact text.
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook readiness approve

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PASS   DOR-001
    #           - assessed at 9/10 ...   - approved by you@example.com
    #           - an acceptable score and a human decision were both required;
    #             neither would have been enough alone
    #           rests on  assessment: 9/10 by ... under spec-readiness@1.0.0
    #           rests on  human-attestation: approved by ... under spec-readiness@1.0.0
    #    PATH STATUS   ON PATH                                  exit 0

    git checkout demo-spellbook/MISSION.md

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

    python3 -m pytest golden-thread-cli/tests claude-code-adapter/tests -q

## Exit codes

    0   ON PATH, or INCOMPLETE (nothing verified yet)
    1   OFF PATH
    2   the command itself could not run
    3   STALE: evidence exists but no longer describes this project
    4   NOT READY: a readiness requirement is not satisfied
