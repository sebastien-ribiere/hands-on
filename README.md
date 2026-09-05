# Golden Thread

A golden path an organisation can distribute, version, and verify.

**Spike 1** proved the vertical slice: a project attaches itself to a versioned
Golden Thread, knows which version and profile it is on, runs a real
architecture rule, and goes **OFF PATH** when it breaks it.

**Spike 2** makes every verdict accountable. There is no `architecture: true`
anywhere. A status is only ever reported together with the *evidence* it came
from — and evidence that no longer describes the work or the requirement is reported as **STALE**
rather than quietly reused.

**Spike 3** adds a minimal Claude Code adapter, proving the core is usable
from inside a real Claude Code session without moving any Golden Thread logic
into Claude Code. See [`claude-code-adapter/README.md`](claude-code-adapter/README.md).

**Spike 4** adds a **Definition of Ready** — the first requirement Golden Thread
cannot verify by itself. `DOR-001` is satisfied by two claims made elsewhere: an
assessment produced against a versioned rubric, and a decision made by a person.
Neither is sufficient alone, and the CLI produces neither.

**Spike 5** completes the thread: a **Definition of Done** with five
requirements and five genuinely different kinds of evidence, a **real security
analyser**, and a **GitLab pipeline that replays the whole verification with no
agent anywhere in it**.

The core is still stdlib-only Python with no dependency on any AI harness. The
assessment arrives from outside it; the rubric is data in the corporate policy;
the analyser is a subprocess the policy names.

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

## The Definition of Done

Five requirements, and five deliberately different kinds of evidence. The
point is not that there are five — it is that a Definition of Done contains
things a machine can settle, things it can only report on, and at least one
thing it can never touch, and that all three keep the same standing.

| Requirement | Evidence provider | What it actually establishes |
|---|---|---|
| `TEST-001` | a deterministic command | a named argv ran over named files and exited zero |
| `ARCH-001` | the real import graph | no protection module imports Fire |
| `SEC-001` | **bandit**, a real analyser | that analyser found nothing it recognises at MEDIUM or above |
| `DOC-001` | a digest stamp in the document | somebody re-stamped the document against this exact code |
| `COOKIE-001` | a person's word | somebody said it, and who they were |

There is no separate "Definition of Done" object in the model, and there does
not need to be one: the profile `academy-spells-done` is the contract, read at
two moments. `DOR-001` reports `NOT READY` because the work was never agreed;
the other five report `OFF PATH` because something in the work is not done.

### Tests: an exit code, and no more than that

`TEST-001` uses the `external_command` engine. The corporate policy declares an
**argv list** — never a string, so no shell is involved and nothing can be
quoted, expanded or split into something else — and the exit code is the
verdict.

    command = ["python3", "-m", "pytest", "-q", "tests"]

The argv is recorded in the evidence `method`, because `external_command` does
not describe a method: running the test suite and running something else are
the same engine and different methods.

What it claims is narrow and the rule says so in its own rationale: a named
command ran against named files and exited zero. **An empty suite exits zero
too.** Requiring the tests to be meaningful is a different requirement, and it
would need a different engine rather than a stricter reading of this one.

A command that could not run at all — missing binary, timeout — is `ERROR`,
never `FAIL` and never `PASS`. And a command that exits zero over a subject
matching no files is `ERROR` as well: a pass over nothing is exactly the
failure mode this project exists to remove.

### Security: a real analyser, and the policy's threshold on top

`SEC-001` runs **bandit**, pinned at 1.9.4. Golden Thread does not reimplement
it, restate its findings, or soften them:

    src/spells/protection/ward.py:21
      MEDIUM B307 (bandit): Use of possibly insecure function - consider using safer ast.literal_eval.
      https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b307-eval

The analyser's rule id, severity, words and reference are copied out unchanged.
Exactly one field is Golden Thread's own — `blocking` — and it is not an
opinion about the finding, it is whether *this profile's* threshold makes it a
failure:

    fail_on_severity = "MEDIUM"
    min_confidence   = "MEDIUM"

Both live in the corporate policy, so "MEDIUM and above fails here" is a
statement the organisation made and versioned. **Findings below the threshold
are still recorded**, marked `blocking: false`, with a note saying how many were
set aside and under which threshold. A scanner whose output is filtered before
anyone sees it is how a security requirement becomes decoration.

The exit code is deliberately *not* the verdict here, because a scanner that
found something and a scanner that crashed both exit non-zero. Anything other
than "ran cleanly" or "ran and found things" is `ERROR`, as is an unreadable
report, and as is a report listing files the analyser could not parse — `PASS`
over code nothing looked at is a claim about unexamined code.

`security_scan` reads one report format today (`format = "bandit"`), and an
unknown format is an `ERROR` naming what is supported. That is one branch, not
a plugin system.

### Documentation: the mechanism, chosen explicitly

"The documentation is updated" is easy to put in a Definition of Done and hard
to mean anything by. Three readings were considered:

- **the doc exists / every function has a docstring.** Checkable, and it
  measures presence rather than currency. A docstring written two years ago
  passes forever.
- **the docs changed in the same commit as the code.** Makes Git the
  mechanism, which this project has refused since Spike 2: a worktree with
  uncommitted work is not identified by its HEAD.
- **the document states which code it describes, and that statement is
  checked.** This is the one.

`docs/ARCHITECTURE.md` carries a line:

    <!-- golden-thread: describes src/ sha256:cdd324e7312c… -->

The engine recomputes the digest of `src/**/*.py` and compares. Different, and
it says so with both digests:

    FAIL   DOC-001  The documentation describes the code that ships
           - docs/ARCHITECTURE.md describes src/ at cdd324e7312c
           - src/ is now at 17f84e2b32c7
           - the code moved and the documentation did not say so

This is Spike 2's own mechanism turned outward. The subject covers **both** the
document and the code, so either moving makes the recorded verdict stale.

**What it proves, stated plainly:** that somebody re-stamped the document
against this exact code. Not that they read it, not that the prose is right.
`golden-thread docs stamp` takes one second and is cheap on purpose — a gate
expensive enough to resent is a gate people route around. What the requirement
removes is the *silent* case, where code ships and nobody has even claimed to
have looked at the documentation since. The CLI says exactly this every time it
stamps, and the engine repeats it in the notes of a `PASS`.

### Cookies: the requirement nothing can check

`COOKIE-001` requires that cookies were prepared and shared with the team. It is
a deliberately unexpected house rule, and it is doing real work.

Every organisation's Definition of Done contains at least one item no scanner,
test suite or model can establish: the demo was walked through with the right
people, the on-call rota was told before the deploy, the customer was warned
about the migration window. They are unverifiable in exactly the way cookies
are. A tool that could only express what it can compute would quietly push
those out of the Definition of Done — not by arguing against them, just by
having nowhere to put them.

So the requirement sits in the profile with the same standing as the
architecture rule, and is satisfied by `golden-thread attest COOKIE-001`:

    COOKIE-001  Cookies were prepared and shared with the team
    Claim         Cookies have been prepared and shared with the team for this delivery.
    Subject       10 file(s) sha256:cdd324e7312c
    Attestor      seb@academy.invalid

    This records that YOU attested this, on your own account.
    Nothing here checked it. Nothing here can: that is why this
    requirement is satisfied by a name rather than by a verdict.

    Type the phrase to confirm: attest cdd324e7312c

Same confirmation discipline as Spike 4's approval, sharing the same code path
so neither can drift into being the lax one, and with the same honest limit: it
makes the claim a deliberate act tied to this exact version of the work. **It
does not prove a human made it.** The attestation expires when `src/` changes —
new work, new cookies.

Spike 4 chose `readiness approve` over a generic `attest`, on the grounds that
one instance is not a pattern. This is the second instance and a different act,
so `attest` exists now and `readiness` is untouched: a Definition of Ready
still needs its rubric, its score and its assessment, and none of that belongs
here.

Two structural guards, in the same spirit as the Spike 4 one: no `SKILL.md` may
run `golden-thread attest`, and none may run `golden-thread docs stamp`. Both
are enforced by a test that parses the shell fences out of every skill file.

## Evidence

One record per requirement, answering six questions and nothing more:

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

### Where each artefact lives, and why

    golden-thread.json                  committed    which policy this project is on
    golden-thread-attestations.json     committed    what we were told, and by whom
    .golden-thread/source/              disposable   the policy cache
    .golden-thread/evidence.json        disposable   what the tool proved

The split is by **what can be rebuilt**. `verify` reproduces the evidence and
the manifest reproduces the cache. An attestation is the one artefact in this
system nothing can regenerate: delete it and the only recourse is to go and ask
a person again.

It also has to *travel*. Spike 4 kept attestations inside `.golden-thread/`,
and the GitLab pipeline is what exposed that as a bug: a runner that cannot see
the approval reports agreed work as un-agreed, which is true of that machine
and false of the project. The contrast showed up inside a single pipeline run —
`DOC-001` passed, because its claim lives in a committed Markdown file, while
`DOR-001` and `COOKIE-001` failed, because theirs did not.

Committing an attestation makes it visible to CI and visible in review. It does
**not** make it authenticated, and nothing here claims otherwise.

### Freshness: the work and the requirement, independently

Freshness has two independent axes. A record remains current only while both
the subject it describes and the requirement it answered are unchanged.

The **subject digest** is a `sha256` over the sorted `(relative path,
sha256(content))` pairs of the exact files the check engine read. `status`
re-identifies that subject. Editing, adding or removing one of those files makes
the evidence STALE; changing an unrelated file does not.

The **requirement fingerprint** identifies the semantics of the individual
requirement: its rule data plus policy artefacts it explicitly pins, such as a
readiness rubric. A move from `v0.2.0` to `v0.3.0`, or from one profile to
another, does not invalidate evidence merely because the container changed. If
`DOR-001` and its rubric are unchanged, its evidence can remain current while
the new profile adds `TEST-001`, `SEC-001`, `DOC-001` and `COOKIE-001`.

The Git ref, resolved revision and profile are still recorded as provenance.
They are not the identity of a requirement. For evidence written before
`requirementFingerprint` existed, Golden Thread keeps the old conservative
behaviour: a profile or policy revision change makes that legacy record STALE
because semantic equivalence cannot be established after the fact.

A Git revision on the subject is descriptive only. A worktree with uncommitted
work is not identified by its HEAD, and a project is not always its own
repository.

## Path status

| Status | Meaning | Exit |
|---|---|---|
| `INCOMPLETE` | nothing has been verified yet | 0 |
| `ON PATH` | every requirement has current, passing evidence | 0 |
| `OFF PATH` | a requirement failed, on evidence that still applies | 1 |
| `NOT READY` | a readiness requirement is not satisfied | 4 |
| `STALE` | evidence exists but no longer describes the current subject or requirement | 3 |

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

## GitLab CI: the verification, replayed by something that cannot think

    .gitlab-ci.yml

One job. It installs the project's toolchain, restores the **pinned** policy
from the committed manifest, runs `golden-thread verify`, and keeps the
machine-readable report as an artifact.

**No agent is involved.** No Claude Code, no model, no network call to anything
that thinks. That independence is the whole point: evidence produced inside an
agent's session is evidence about that session. The pipeline does not import
the adapter, does not read a skill, and would run identically on a machine
where Claude Code has never been installed.

**It never runs `init`.** `init` re-resolves a ref, and a tag can move. The job
reads the commit recorded in `golden-thread.json` and restores exactly that,
printing it so the log says which policy this run was held to.

**The artifact is kept `when: always`.** The run that fails is the run whose
report somebody will want to read.

### Computing the state, and deciding to block, are two different things

The pipeline keeps them visibly apart, in one job:

    # 1. compute the state. Never fails the job on a verdict.
    - |
      set +e
      $GT -C "$GT_PROJECT" verify --json > golden-thread-report.json
      gt_exit=$?
      set -e

    # 3. this project's policy. THIS is the line that blocks a merge.
    - exit $gt_exit

Golden Thread computes `OFF PATH`. It does not ask for a red pipeline. The
`exit` line does, and it is one editable line with a comment saying so. A
project pinning the same golden path may choose otherwise — that is what "not a
prison" means once it reaches a pipeline.

A failing job says which of the two happened:

    PIPELINE FAILED BY THIS PROJECT'S POLICY.
    Golden Thread computed a state and did not ask for this.
    The line in .gitlab-ci.yml that propagates its exit code did.
    A project pinning the same golden path may choose otherwise.

and, distinctly, for exit code 2:

    PIPELINE FAILED: golden-thread could not run at all.
    This is not a verdict about the code. Nothing was verified.

### Running the pipeline without GitLab

    ./demo/run-ci-locally.sh

This is not a simulation. `demo/gitlab_job.py` reads `.gitlab-ci.yml`, takes
the `image`, `before_script` and `script` GitLab would run, assembles them into
one shell script the way the runner does — so a variable set on one line is
still set on the next — and runs them **in that image, under Docker**. Break
the pipeline and this breaks with it. A demo that reimplemented the steps in
bash would keep working after the pipeline stopped.

It stages a clean copy of the repository so nothing it does touches your
working tree, and refuses to run at all without Docker rather than substituting
something that merely resembles the image.

One fidelity gap, stated because it matters for what this proves: GitLab checks
out a commit, while this helper stages the current working tree. For a faithful
rehearsal, commit the delivery state first — including
`demo-spellbook/golden-thread-attestations.json`. The helper does not pretend an
uncommitted working tree is the same thing as a GitLab checkout.

## Layout

    .gitlab-ci.yml           the pipeline: verify, report, and one line that decides to block

    golden-thread-source/    corporate source of authority — POLICY only, versioned by Git tag
      golden-thread.toml       catalog: schema version, default profile
      profiles/                which rules a profile enforces
      rules/ARCH-001.toml      the declarative architecture rule
      rules/DOR-001.toml       the Definition of Ready: rubric pinned, thresholds set
      rules/TEST-001.toml      the test suite: an argv, and an exit code
      rules/SEC-001.toml       bandit, and the Academy's severity threshold
      rules/DOC-001.toml       the documentation stamp
      rules/COOKIE-001.toml    the requirement nothing can check
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
        attest.py              record a claim no tool can check
        docs.py                stamp a document with the code it describes
        checks/importgraph.py  the real import graph
        checks/layered_dependencies.py   the architecture check engine
        checks/spec_readiness.py         the readiness engine — reads claims, runs no check
        checks/subprocess_engine.py      argv, declared subjects, and "could not run"
        checks/external_command.py       a command, and its exit code
        checks/security_scan.py          a real analyser, and the policy's threshold
        checks/doc_stamp.py              the documentation stamp
        checks/human_attestation.py      a person's word, and nothing else
      tests/

    demo-spellbook/          a consumer project
      golden-thread.json       the manifest: committed, and what CI reads
      golden-thread-attestations.json   committed — human claims travel to CI and review
      MISSION.md               what DOR-001 is about, digested by content
      src/                     the spells
      tests/                   what TEST-001 runs
      docs/ARCHITECTURE.md     what DOC-001 stamps
      .golden-thread/          disposable: policy cache and evidence
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

`verify` produces evidence; `status` only reads it. Re-identifying a subject and
recomputing a requirement fingerprint are not producing evidence: `status` runs
no check, it establishes whether what was recorded still applies.

## Reproducing the demonstration

Three demonstrations. Spike 1–2 — attach, verify, invalidate, repair:

    ./demo/run-demo.sh

Spike 4 — the Definition of Ready, from NOT READY to READY:

    ./demo/run-dor-demo.sh

Spike 5 — the Definition of Done, every failure path, and the pipeline:

    ./demo/run-dod-demo.sh

That last one walks the project through green, an architecture violation, a
real security defect, a missing attestation, repair after each, and finishes by
running the actual GitLab job in Docker. It needs Docker and network access on
first run: `demo/install-toolchain.sh` builds a disposable venv with pytest and
bandit in `.demo/venv`, and the pipeline pulls `python:3.12-slim`.

Or step by step, from the repository root:

    # 0. publish the corporate Golden Thread as a tagged Git repository.
    #    v0.1.0 is the golden path before the DoR; v0.2.0 adds it.
    ./demo/publish-source.sh

    # 1. attach the project
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook \
        init --source "../.demo/golden-thread-source" --ref v0.1.0

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
        --source "../.demo/golden-thread-source" --ref v0.2.0 \
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

### The Definition of Done, step by step

    # 0. the corporate golden path, and the project's own toolchain
    ./demo/publish-source.sh          # v0.1.0, v0.2.0, v0.3.0
    ./demo/install-toolchain.sh       # pytest and bandit, into .demo/venv
    export PATH="$PWD/.demo/venv/bin:$PATH"

    # 1. attach to the profile carrying the whole contract
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook init \
        --source "../.demo/golden-thread-source" --ref v0.3.0 \
        --profile academy-spells-done

    # 2. six requirements, and the headline answers the first question first
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PATH STATUS   NOT READY                                exit 4

    # ... satisfy the Definition of Ready as above ...

    # 3. now the question has changed: is it finished?
    #    PATH STATUS   OFF PATH                                 exit 1
    #    FAIL   DOC-001    - docs/ARCHITECTURE.md carries no golden-thread stamp
    #    FAIL   COOKIE-001 - nobody has attested this

    # 4. the document says which code it describes
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook docs stamp

    # 5. and somebody made the cookies
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook attest COOKIE-001 --show
    ./golden-thread-cli/bin/golden-thread -C demo-spellbook attest COOKIE-001 \
        --attestor "you@example.com" --note "Chocolate chip. 24 of them."
    #    Type the phrase to confirm: attest cdd324e7312c

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    PATH STATUS   ON PATH                                  exit 0

    # 6. a real security defect: a ward that evaluates what it is handed
    printf '\n\ndef improvise(i):\n    return eval(i)\n' \
        >> demo-spellbook/src/spells/protection/ward.py

    ./golden-thread-cli/bin/golden-thread -C demo-spellbook verify
    #    FAIL   SEC-001
    #           src/spells/protection/ward.py:21
    #             MEDIUM B307 (bandit): Use of possibly insecure function ...
    #    FAIL   DOC-001    - the code moved and the documentation did not say so
    #    FAIL   COOKIE-001 - attested about a different version of the work
    #    PATH STATUS   OFF PATH                                 exit 1

One edit, three requirements. `ARCH-001` still passes — the import graph is
untouched — while the analyser finds the defect, the stamp stops describing the
code, and the attestation stops describing the work. A claim is tied to what it
was made about, for a person exactly as for a rule.

    # 7. repair, re-stamp, re-attest
    git checkout demo-spellbook/src/spells/protection/ward.py

    # 8. and the pipeline replays the whole thing, with no agent
    ./demo/run-ci-locally.sh

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

Run the suites separately:

    python3 -m pytest golden-thread-cli/tests -q
    python3 -m pytest claude-code-adapter/tests -q

Both directories contain a package-less `conftest.py`; combining them in one
pytest invocation can bind the second suite to fixtures from the first. The
adapter README documents the same constraint.

The security suite runs bandit for real and skips that integration check — it
does not fake it — when bandit is not installed. A parser that agrees with its
own fixture and disagrees with the tool proves nothing.

`test_record_compatibility.py` loads literal older evidence shapes. Additive
fields such as `findings`, `blocking`, `command` and
`requirementFingerprint` keep conservative defaults so old records still load;
legacy records without a fingerprint retain conservative freshness semantics.

## Exit codes

    0   ON PATH, or INCOMPLETE (nothing verified yet)
    1   OFF PATH
    2   the command itself could not run
    3   STALE: evidence exists but no longer describes the current subject or requirement
    4   NOT READY: a readiness requirement is not satisfied
