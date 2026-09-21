"""Optional French presentation, without changing policy or recorded evidence.

GOLDEN_THREAD_LANG=fr selects the lab's human output. JSON, verdicts, command
names, confirmation phrases, analyser findings and user-authored text stay raw.
Unknown policy wording falls back to the original rather than guessing a meaning.
"""

import os
import re
from string import Formatter

from ._fr import RECORDED, TEXT


def french() -> bool:
    return os.environ.get("GOLDEN_THREAD_LANG", "en").lower().split("_")[0].split("-")[0] == "fr"


def t(message: str, *values) -> str:
    translated = TEXT.get(message, message) if french() else message
    return translated.format(*values) if values else translated


def _pattern(template: str):
    parts = []
    for literal, field, _, _ in Formatter().parse(template):
        parts.append(re.escape(literal))
        if field is not None:
            parts.append(r"(.*?)")
    return re.compile("".join(parts), re.DOTALL)


_RECORDED_PATTERNS = [(_pattern(en), fr) for en, fr in RECORDED.items() if "{0}" in en]


def recorded_text(message: str) -> str:
    """Translate only known engine explanations, at the display boundary.

    Matching is against the complete message; captured paths, identities,
    digests and comments are inserted unchanged. Never call on scanner output.
    """
    if not french():
        return message
    if message in RECORDED:
        return RECORDED[message]
    for pattern, translated in _RECORDED_PATTERNS:
        match = pattern.fullmatch(message)
        if match:
            return translated.format(*match.groups())
    if "\n" in message:
        return "\n".join(recorded_text(line) for line in message.split("\n"))
    return message


def claim_summary(claim) -> str:
    if not french():
        return claim.summary()
    under = f" selon {claim.rubric}" if claim.rubric else " sur sa seule déclaration"
    value = f"{claim.score if claim.score is not None else '?'}/10" if claim.kind == "assessment" else t(claim.decision or "sans décision")
    return f"{value} par {claim.actor}{under}"


def method_text(method) -> str:
    if not french():
        return str(method)
    command = f" [{' '.join(method.command)}]" if method.command else ""
    return f"{method.check}{command} - {method.profile} - policy {method.policy_ref} @ {method.policy_revision[:12]}"
