"""Protection spells: what they do, and what they draw on."""

from spells.protection import shield, ward


def test_shield_raises_a_barrier_from_air():
    assert shield.cast(3) == "shield raised: a gust of wind at strength 3"


def test_shield_absorbs_by_deflecting():
    assert shield.absorb("an arrow") == "an arrow is pushed aside by air"


def test_ward_sets_a_mist_from_water():
    assert ward.cast(5) == "ward set: a mist of density 5"


def test_ward_smothers_rather_than_deflects():
    assert ward.smother("a flame") == "a flame is quenched by water"
