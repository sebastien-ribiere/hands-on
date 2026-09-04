"""Offensive spells, which may draw on Fire freely.

ARCH-001 binds the protection layer, not the word "fire". These tests exist so
that a change breaking that distinction fails here as well as there.
"""

from spells.offense import flame_lance


def test_flame_lance_draws_on_fire():
    assert flame_lance.cast(7) == "flame lance loosed: a flame at heat 7"


def test_flame_lance_scorches_its_target():
    assert flame_lance.strike("a troll") == "a troll is scorched"
