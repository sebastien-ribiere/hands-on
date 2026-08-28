"""An offensive spell that legitimately draws on Fire.

This module exists to prove ARCH-001 is a real architecture rule and not a
global ban on the word "fire": it depends on spells.elements.fire and stays
compliant, because it is not in the protection layer.
"""

from spells.elements import fire


def cast(heat: int = 7) -> str:
    return f"flame lance loosed: {fire.ignite(heat)}"


def strike(target: str) -> str:
    return fire.scorch(target)
