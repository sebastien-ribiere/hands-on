"""Stamping a document with the code it describes.

`golden-thread docs stamp` writes one line into a document:

    <!-- golden-thread: describes src/ sha256:<64 hex> -->

and that is the whole command. It is cheap on purpose. The requirement it
satisfies (DOC-001, engine `doc_stamp`) claims only that somebody re-stamped
this document against this exact code -- not that they read it, and not that
the prose is right. Making the stamp expensive would not make the claim
stronger; it would only make people avoid the requirement, and a Definition of
Done nobody runs is worth less than a modest one they do.

The command is resolved by engine name rather than by requirement id: this CLI
knows nothing about DOC-001, only that a profile may pin a rule checked by
`doc_stamp`, the same way `readiness` finds its rule by engine and never by id.
"""

from pathlib import Path

from . import policy, source
from .checks import doc_stamp
from .errors import GoldenThreadError


class Target:
    def __init__(self, rule, document: Path, describes: str):
        self.rule = rule
        self.document = document
        self.describes = describes


def resolve(project: Path, manifest, requirement: str | None = None) -> Target:
    source_root = source.ensure_available(project, manifest)
    profile = policy.load_profile(source_root, manifest.profile)
    candidates = [rule for rule in profile.rules if rule.check == doc_stamp.NAME]

    if requirement is not None:
        candidates = [rule for rule in candidates if rule.id == requirement]
        if not candidates:
            raise GoldenThreadError(
                f"profile {profile.name!r} has no documentation requirement "
                f"{requirement!r}"
            )
    if not candidates:
        raise GoldenThreadError(
            f"profile {profile.name!r} enforces no documentation requirement, "
            "so there is nothing to stamp"
        )
    if len(candidates) > 1:
        raise GoldenThreadError(
            f"profile {profile.name!r} has several documentation requirements "
            f"({', '.join(r.id for r in candidates)}); name one"
        )

    rule = candidates[0]
    return Target(
        rule,
        project / str(rule.params["document"]),
        str(rule.params.get("describes", "src")),
    )


def stamp(project: Path, target: Target) -> tuple[str, bool]:
    """Write the current stamp into the document. Returns (stamp, changed).

    A document that does not exist yet is refused rather than created: the
    golden path asks a team to document their code, and a file containing
    nothing but a digest would satisfy the letter of that while emptying it.
    """
    if not target.document.is_file():
        raise GoldenThreadError(
            f"there is no {target.document.relative_to(project).as_posix()} to "
            "stamp. Write the documentation first: a stamp on an empty page is "
            "a claim about nothing"
        )

    line = doc_stamp.expected_stamp(target.rule, project)
    text = target.document.read_text(encoding="utf-8")
    existing = doc_stamp.read_stamp(text)

    if existing is not None:
        old = doc_stamp.STAMP.search(text)
        if old.group(0) == line:
            return line, False
        updated = text[: old.start()] + line + text[old.end():]
    else:
        separator = "" if text.endswith("\n") else "\n"
        updated = f"{text}{separator}\n{line}\n"

    target.document.write_text(updated, encoding="utf-8")
    return line, True
