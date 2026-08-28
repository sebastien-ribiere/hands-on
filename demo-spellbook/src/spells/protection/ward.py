"""A ward that smothers an attack rather than turning it aside.

Uses a relative import on purpose: the Golden Thread architecture check
resolves relative imports to absolute module paths, so this dependency is
seen exactly as `spells.elements.water`.
"""

from ..elements import water


def cast(density: int = 5) -> str:
    return f"ward set: {water.mist(density)}"


def smother(attack: str) -> str:
    return water.quench(attack)
