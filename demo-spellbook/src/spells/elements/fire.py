"""The Fire element.

Destructive. Offensive spells may draw on it. Protection spells may not:
see ARCH-001 in the Golden Thread.
"""


def ignite(heat: int) -> str:
    return f"a flame at heat {heat}"


def scorch(target: str) -> str:
    return f"{target} is scorched"
