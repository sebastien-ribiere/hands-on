# Claude Code adapter

**Spike 3** proves Golden Thread is usable from inside a real Claude Code
session, without moving any Golden Thread logic into Claude Code. The core
still doesn't know Claude Code exists -- `golden-thread-cli/tests/
test_core_is_harness_agnostic.py` still passes, untouched, and this directory
is the only thing that changed.

## Contract: core -> adapter

Nothing new was added to the core. This adapter is built entirely on the
contract Spike 1 and Spike 2 already shipped:

    golden-thread -C <project> status --json

That one command is the whole interface. It answers, in one JSON document:
which Golden Thread (`ref`, `profile`), and the current `pathStatus`
(`ON PATH` / `OFF PATH` / `STALE` / `INCOMPLETE`) with, per requirement, the
exact reason it isn't `PASS` (`freshness.reasons`, or the `violations` in
`evidence.result`).

The adapter deliberately never calls `verify`. `status` re-identifies the
subject by digest but runs no check -- it's cheap enough to call before every
session and before every edit. `verify` runs the actual check engine and
produces new evidence; triggering that silently from a hook, on every
keystroke, is exactly the kind of thing Spike 2 built the evidence model to
prevent ("no silent reuse", and no silent *production* either). Verification
stays a decision the developer makes on purpose, by typing
`golden-thread verify`.

## Hooks used, and why

Two Claude Code hooks, both read-only against `status --json`, both
non-blocking by construction:

- **`SessionStart`** -- runs once when a session opens on a Golden
  Thread-attached project. Emits `hookSpecificOutput.additionalContext`
  (and a matching `systemMessage`) with the version, profile and status.
  This is "the context minimal nécessaire" from the brief: three lines,
  shown once, not injected into every turn.

- **`PreToolUse`**, matched on `Edit|Write` -- runs before a file change.
  If the path is not `ON PATH`, it emits the same kind of message, framed as
  `GOLDEN THREAD DEVIATION`, listing what's missing per requirement. It
  always sets `permissionDecision: "allow"` (see below) and always exits 0.

No other hook was needed. `PostToolUse` was considered (to confirm a check
still passes right after an edit) and rejected for this spike: `status`
alone, called again at the next `SessionStart` or `PreToolUse`, already
re-establishes freshness from the digest -- a third call point would be
duplication, not new information.

`statusLine` was considered as an alternative to `SessionStart` for a
persistent "always visible" status. Not used here: it would need a second
moving part (a cache file written by one hook and read by the status line
script) for a spike whose brief only asks the context to appear naturally at
session start. Worth revisiting if Golden Thread status needs to survive a
long session without a fresh look, which SessionStart alone won't catch --
this is now an open question in memory, not something built.

## Why the adapter can't gate

`PreToolUse` hooks *can* deny a tool call (`permissionDecision: "deny"`, or
exit 2). This adapter's code never uses either. That's asserted, not just
described: `tests/test_adapter_is_isolated.py` greps `hooks/*.py` for
`"deny"`/`"ask"` and for any `return` of a non-zero exit code, and fails the
suite if either appears. The "not a prison" stance from the core's own
framing is enforced the same way the core enforces its own harness-agnosticism
on itself -- a test that would fail the moment someone tried to add a block.

## What stays harness-agnostic vs. what is Claude Code-specific

Harness-agnostic (lives in `golden-thread-cli/`, untouched by this spike):
the evidence model, the freshness/staleness logic, the `layered_dependencies`
check, the `status --json` report shape, all exit codes.

Claude Code-specific (lives only here, in `claude-code-adapter/`):

- the two hook scripts and their `hookSpecificOutput` shape;
- the translation from `pathStatus` / `reportedStatus` / `freshness.reasons`
  into the two lines of prose Claude Code shows (`lib/render.py`);
- `.claude/settings.json` in the consumer project, which registers the
  hooks.

No corporate rule, no ARCH-001 knowledge, no policy concept lives in this
adapter. It knows five field names from the JSON report and nothing about
what they mean.

## A real name collision, worth knowing about

This machine already has a *different, unrelated* `golden-thread` package on
PATH (`pip show golden-thread` -> `/home/seb/src/AI/golden-thread`, an "AI
golden path CLI for platform teams"). A bare `golden-thread` command is not
guaranteed to be this project's CLI here. `lib/golden_thread_client.py`
therefore resolves the binary from `$GOLDEN_THREAD_BIN` if set, falling back
to the bare command otherwise -- and the demo's `.claude/settings.json` sets
that variable explicitly to this repo's own
`golden-thread-cli/bin/golden-thread`. A real install of this tool (via
`pip install -e golden-thread-cli`, as the top-level README documents) would
not have this collision; this is a fact about the machine the spike was built
on, not about the design.

## Installing the adapter into a project

1. Attach the project to a Golden Thread (`golden-thread init ...`), as
   already documented in the top-level README.
2. Add `.claude/settings.json` registering the two hooks, pointed at this
   directory's `hooks/session_start.py` and `hooks/pre_tool_use.py`. See
   `demo-spellbook/.claude/settings.json` for the exact, working example
   used in the demo below.

## Reproducing the demonstration

Deterministic, no live model call -- feeds the hooks the exact stdin JSON
Claude Code sends, and reads their stdout JSON:

    cd demo-spellbook
    ../golden-thread-cli/bin/golden-thread verify   # ON PATH baseline

    # SessionStart: context appears
    CLAUDE_PROJECT_DIR="$PWD" bash -c \
      'GOLDEN_THREAD_BIN="${CLAUDE_PROJECT_DIR}/../golden-thread-cli/bin/golden-thread" \
       python3 "${CLAUDE_PROJECT_DIR}/../claude-code-adapter/hooks/session_start.py"' \
      <<< "{\"cwd\": \"$PWD\"}"
    #   {"hookSpecificOutput": {..., "additionalContext":
    #     "Golden Thread v0.1.0\nProfile: academy-spells\nStatus: ON PATH"}, ...}

    # PreToolUse on Edit while ON PATH: silent
    CLAUDE_PROJECT_DIR="$PWD" bash -c \
      'GOLDEN_THREAD_BIN="${CLAUDE_PROJECT_DIR}/../golden-thread-cli/bin/golden-thread" \
       python3 "${CLAUDE_PROJECT_DIR}/../claude-code-adapter/hooks/pre_tool_use.py"' \
      <<< "{\"cwd\": \"$PWD\", \"tool_name\": \"Edit\"}"
    #   (nothing printed, exit 0)

    # break ARCH-001
    printf '\nfrom ..elements import fire\n' >> src/spells/protection/ward.py
    ../golden-thread-cli/bin/golden-thread verify   # OFF PATH

    # PreToolUse on Edit while OFF PATH: signals, still allows
    CLAUDE_PROJECT_DIR="$PWD" bash -c \
      'GOLDEN_THREAD_BIN="${CLAUDE_PROJECT_DIR}/../golden-thread-cli/bin/golden-thread" \
       python3 "${CLAUDE_PROJECT_DIR}/../claude-code-adapter/hooks/pre_tool_use.py"' \
      <<< "{\"cwd\": \"$PWD\", \"tool_name\": \"Edit\"}"
    #   {"hookSpecificOutput": {..., "permissionDecision": "allow",
    #     "additionalContext": "GOLDEN THREAD DEVIATION\nYou are leaving the
    #     supported path.\nMissing: ARCH-001 -- spells/protection/ward.py:18
    #     spells.protection.ward -> spells.elements.fire\nRun: golden-thread
    #     status"}, ...}

    # repair
    git checkout -- src/spells/protection/ward.py
    ../golden-thread-cli/bin/golden-thread verify   # ON PATH again

A real Claude Code session, driven the same way (also run for this spike, see
the REVIEW PACKET for the transcripts):

    cd demo-spellbook
    claude -p "In one short sentence, based only on the Golden Thread \
context you were given at the start of this session, what is the current \
Golden Thread status and profile?"
    # -> "Golden Thread is at v0.1.0, profile academy-spells, status ON PATH."

    printf '\nfrom ..elements import fire\n' >> src/spells/protection/ward.py
    ../golden-thread-cli/bin/golden-thread verify
    claude -p "Append the exact line '# reviewed' to the end of README.md. \
Before you do, tell me in one sentence whether Golden Thread flagged \
anything about this project." --permission-mode acceptEdits
    # -> the edit lands (not blocked); the model reports the deviation was
    #    flagged and correctly reads it as unrelated to the edit it just made

    git checkout -- README.md src/spells/protection/ward.py
    ../golden-thread-cli/bin/golden-thread verify

## Tests

    python3 -m pytest claude-code-adapter/tests -q

13 tests: SessionStart's context in each path state, PreToolUse's silence on
`ON PATH` and its message (never a denial) in every other state, and the two
structural guards described above.

Run this suite and `golden-thread-cli/tests` as two separate `pytest`
invocations, not one combined command: both directories have a same-named,
package-less `conftest.py`, and pytest's default import mode caches the first
one it loads under the module name `conftest`, so a single invocation covering
both silently binds the second suite to the wrong fixtures.

## Testing the core still works with no harness at all

Nothing in `golden-thread-cli/` was touched by this spike.

    python3 -m pytest golden-thread-cli/tests -q

51 tests, unchanged, still green -- including
`test_core_is_harness_agnostic.py`, which greps the core's source for any
reference to `claude`, `anthropic`, `.mcp`, `copilot` or `cursor` and fails
if it finds one.

## Known limitation, not built here

`PreToolUse` reports the *project's* path status, not the status of the file
being edited. Editing `README.md` while `ward.py` is `OFF PATH` still shows
the deviation banner -- confirmed live in the demo above, where the model
correctly called it "unrelated noise" for that specific edit. Scoping the
signal to files a rule actually reads would need the adapter to know which
files each requirement's subject covers, which `status --json` does not
expose today (only a digest, not a file list). Left as an open question
rather than built.
