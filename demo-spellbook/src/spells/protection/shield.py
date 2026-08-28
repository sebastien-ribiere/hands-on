"""A shield that turns an incoming attack aside."""

from spells.elements.air import deflect, gust


def cast(strength: int = 3) -> str:
    barrier = gust(strength)
    return f"shield raised: {barrier}"


def absorb(attack: str) -> str:
    return deflect(attack)
