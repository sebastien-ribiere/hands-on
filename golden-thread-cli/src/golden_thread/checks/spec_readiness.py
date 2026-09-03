"""Check engine: spec_readiness.

A Definition of Ready, expressed as a requirement like any other -- and unlike
any other, because this engine cannot produce its own evidence. It runs no
analysis. It reads two claims made elsewhere and decides whether the *policy's*
conditions on them are met:

  1. an assessment, produced by a model against a versioned rubric;
  2. a human attestation, produced by a person who read that assessment.

Every condition lives in the rule's params, i.e. in the corporate policy, never
here:

    min_score                 the score at or above which an assessment is
                              considered acceptable
    max_blockers              how many open blockers a Ready mission may have
    requires_human_approval   whether a person must still say yes

This engine deliberately has no way to satisfy the requirement on its own. It
holds no model, calls nothing, and invents no score. If `requires_human_approval`
is true and no human attestation is on record, the result is FAIL no matter how
high the score is -- 10/10 included. That is not a safety margin, it is the
statement the requirement is making: a readiness score is one reader's opinion
about a document, and an opinion is not a decision.

Both claims are checked against the subject digest, so neither survives an edit
to the mission they were made about. An approval is given to a specific text,
not to a file name.
"""

from pathlib import Path

from .. import attestation as attestation_mod
from .. import state
from .. import subject as subject_mod
from ..attestation import APPROVED, ASSESSMENT, HUMAN_ATTESTATION, Attestation
from ..errors import GoldenThreadError
from ..results import ERROR, FAIL, PASS, RuleResult
from ..subject import Subject

NAME = "spec_readiness"

DEFAULT_SUBJECT_FILES = ("MISSION.md",)


def _subject_files(rule) -> list[str]:
    declared = rule.params.get("subject_files", list(DEFAULT_SUBJECT_FILES))
    if not isinstance(declared, list) or not declared:
        raise GoldenThreadError(
            "rule params declare no 'subject_files': a readiness requirement "
            "must say which document it is about"
        )
    return [str(entry) for entry in declared]


def rubric_ref(rule) -> str:
    """The rubric this rule pins, as an assessment records it."""
    rubric_id = rule.params.get("rubric")
    version = rule.params.get("rubric_version")
    if not rubric_id or not version:
        raise GoldenThreadError(
            "rule params must declare both 'rubric' and 'rubric_version': an "
            "assessment made under an unnamed rubric cannot be audited"
        )
    return f"{rubric_id}@{version}"


def subject(rule, project: Path) -> Subject:
    """The mission document(s), by content.

    A file that does not exist contributes nothing rather than raising: "the
    mission was not written" is a fact about the subject, and the digest moves
    the moment it appears.
    """
    paths = [project / name for name in _subject_files(rule)]
    return subject_mod.identify(project, project, [p for p in paths if p.is_file()])


def _applies(claim: Attestation, current: Subject, wanted_rubric: str) -> str | None:
    """Why a recorded claim does not describe the situation, or None."""
    if not attestation_mod.describes(claim, current):
        return (
            f"the {claim.kind} was made about a different version of the mission "
            f"({claim.subject.file_count} file(s) {claim.subject.short_digest} -> "
            f"{current.file_count} file(s) {current.short_digest})"
        )
    if claim.rubric != wanted_rubric:
        return (
            f"the {claim.kind} was made under rubric {claim.rubric}, and this "
            f"profile now pins {wanted_rubric}"
        )
    return None


def run(rule, project: Path) -> RuleResult:
    scanned = subject(rule, project)

    try:
        wanted_rubric = rubric_ref(rule)
        _subject_files(rule)
    except GoldenThreadError as exc:
        return RuleResult(status=ERROR, subject=scanned, error=str(exc))

    min_score = int(rule.params.get("min_score", 8))
    max_blockers = int(rule.params.get("max_blockers", 0))
    needs_human = bool(rule.params.get("requires_human_approval", True))

    assessment = state.latest_attestation(project, rule.id, ASSESSMENT)
    approval = state.latest_attestation(project, rule.id, HUMAN_ATTESTATION)
    supporting = tuple(c for c in (assessment, approval) if c is not None)

    notes: list[str] = []
    if scanned.file_count == 0:
        notes.append(
            f"no mission document found: expected {', '.join(_subject_files(rule))}"
        )

    # --- the assessment half --------------------------------------------
    assessment_ok = False
    if assessment is None:
        notes.append(
            "no readiness assessment on record. "
            "Run: golden-thread readiness rubric"
        )
    else:
        stale = _applies(assessment, scanned, wanted_rubric)
        if stale:
            notes.append(stale)
        else:
            score = assessment.score
            blockers = assessment.blockers
            decisions = assessment.decisions
            if score is None:
                notes.append("the recorded assessment carries no score")
            elif score < min_score:
                notes.append(
                    f"assessed at {score}/10, below the {min_score} this profile "
                    f"requires"
                )
            if decisions:
                notes.append(
                    f"{len(decisions)} decision(s) still awaiting a human answer"
                )
            if len(blockers) > max_blockers:
                notes.append(
                    f"{len(blockers)} blocker(s), and this profile allows "
                    f"{max_blockers}: {'; '.join(blockers)}"
                )
            assessment_ok = (
                score is not None
                and score >= min_score
                and len(blockers) <= max_blockers
            )
            if assessment_ok:
                notes.append(
                    f"assessed at {score}/10 against {wanted_rubric}, at or above "
                    f"the {min_score} this profile requires"
                )

    # --- the human half --------------------------------------------------
    # Evaluated on its own, never as a consequence of the score. A high score
    # does not imply approval, and the absence of one is reported as its own
    # reason rather than folded into the assessment's.
    human_ok = not needs_human
    if needs_human:
        if approval is None:
            notes.append(
                "no human approval on record. A readiness score never approves "
                "itself. Run: golden-thread readiness approve"
            )
        else:
            stale = _applies(approval, scanned, wanted_rubric)
            if stale:
                notes.append(stale)
            elif approval.decision != APPROVED:
                note = approval.payload.get("note", "")
                notes.append(
                    f"{approval.actor} recorded '{approval.decision}'"
                    + (f": {note}" if note else "")
                )
            else:
                human_ok = True
                notes.append(f"approved by {approval.actor}")

    satisfied = assessment_ok and human_ok and scanned.file_count > 0
    if satisfied:
        notes.append(
            "an acceptable score and a human decision were both required; "
            "neither would have been enough alone"
        )

    return RuleResult(
        status=PASS if satisfied else FAIL,
        subject=scanned,
        notes=tuple(notes),
        supporting=supporting,
    )
