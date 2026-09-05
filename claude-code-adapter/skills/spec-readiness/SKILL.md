---
name: spec-readiness
description: Assess whether a mission is ready to be worked on, against the versioned rubric the project's Golden Thread publishes, and record the assessment. Use when a mission or spec arrives and before starting implementation, when Golden Thread reports NOT READY, or when the user asks whether something is ready, asks for a readiness assessment, or asks about DOR-001 or a Definition of Ready.
---

# Assessing a mission's readiness

Golden Thread's Definition of Ready is satisfied by two separate claims: an
assessment, and a human decision. **You produce the first one. You must never
produce the second.**

## What you are actually doing

You are giving one reader's opinion about a document, in a structured form,
so that a person can have a better conversation about it. You are not
measuring anything. Another model would score this differently, and so might
you tomorrow. Say so if the user treats the number as a fact.

The score's job is to make the gaps in a mission explicit *before* someone
writes code against them. The gaps matter more than the number.

## Steps

### 1. Read the rubric from the project, never from memory

```bash
golden-thread readiness rubric --json
```

This is policy, pinned by the project's Golden Thread tag. It tells you the
dimensions and what each is worth, the thresholds, the required sections, and
`subjectFiles` — the mission document(s) to assess. Use the dimensions it
returns, not the ones you remember from another project.

If this fails with "no Golden Thread manifest", the project isn't attached to
a Golden Thread; say so and stop.

### 2. Read the mission

Read every file listed in `subjectFiles`. Read the surrounding code too, when
a claim in the mission is checkable against it — a mission that names a module
that already exists differently is a fact worth having.

### 3. Assess

Write JSON in this shape:

```json
{
  "assessor": "<the model and harness doing this, e.g. sonnet via a coding agent>",
  "rubric": "<the exact `rubric` value from step 1>",
  "score": 7,
  "dimensions": [
    {"id": "<dimension id>", "score": 2, "note": "why this many points"}
  ],
  "facts": [],
  "assumptions": [],
  "unknowns": [],
  "unknownUnknowns": [],
  "blockers": [],
  "decisions": []
}
```

Rules the CLI enforces, so getting them wrong means a rejected submission:

- one entry per rubric dimension, no extras, no omissions;
- each dimension score between 0 and that dimension's `points`;
- **the dimension scores must sum to `score`** — the headline number has to
  have an argument underneath it;
- all six sections present; an empty list is a fine answer, a missing key is
  not.

What goes where:

- **facts** — what you verified, in the mission or the code. Not inferences.
- **assumptions** — what you are taking as true without checking. Each one is
  a place this could go wrong quietly.
- **unknowns** — open questions whose answers the implementer could reasonably
  find or choose alone.
- **unknownUnknowns** — where you suspect the mission's frame itself may be
  incomplete. Guessing here is the point; leaving it empty is usually a sign
  you did not look hard enough.
- **blockers** — things that make the work impossible or wrong to start. Under
  most policies a single blocker means not ready at any score.
- **decisions** — questions that need a *human* answer, because the choice is
  theirs and not yours. Write each as the question plus what turns on it.

Keep `decisions` genuinely decision-shaped. "Which element does a frost ward
draw from, given ARCH-001 forbids Fire?" is a decision. "What should the
variable be called?" is not.

### 4. Record it

```bash
golden-thread readiness assess --input <your-assessment.json>
```

### 5. Report, and hand over

Show the user the score, then — more importantly — the decisions and blockers,
as a numbered list they can answer. Then stop.

If `decisions` is non-empty, the useful next step is the user answering them
*in the mission document*, and you re-assessing the rewritten text. The
recorded assessment is tied to the document's content digest, so it correctly
stops applying the moment the mission changes.

## What you must not do

**Never execute `golden-thread readiness approve` on behalf of the user.** That
command records that a named person decided the work should start. It is not
yours to run, at any score, however obvious the answer looks, and however
explicitly the user delegates the click or command to you.

You **may** tell the user the exact approval command they must execute
themselves. The boundary is execution, not discoverability: the person can be
guided to the decision, but the agent does not perform the decision.

Reaching 10/10 changes nothing about this. A readiness score is an assessment;
approval is a decision; the whole requirement exists to keep those two apart.
