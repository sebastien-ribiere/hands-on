"""The elements, on their own."""

from spells.elements import air, fire, water


def test_air_gusts_at_a_strength():
    assert air.gust(7) == "a gust of wind at strength 7"


def test_water_mists_at_a_density():
    assert water.mist(2) == "a mist of density 2"


def test_fire_ignites_at_a_heat():
    assert fire.ignite(9) == "a flame at heat 9"


def test_each_element_answers_an_incoming_attack_its_own_way():
    incoming = "a hurled stone"
    assert air.deflect(incoming).endswith("pushed aside by air")
    assert water.quench(incoming).endswith("quenched by water")
    assert fire.scorch(incoming).endswith("is scorched")
