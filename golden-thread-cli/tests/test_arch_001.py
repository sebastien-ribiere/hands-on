"""ARCH-001 itself: does the rule catch what it must, and only that."""

from golden_thread.checks import layered_dependencies
from golden_thread.policy import Rule
from golden_thread.results import ERROR, FAIL, PASS

RULE = Rule(
    id="ARCH-001",
    title="Protection spells must not depend on Fire",
    check="layered_dependencies",
    params={
        "source_root": "src",
        "layers": [
            {
                "name": "protection",
                "match": "spells.protection",
                "allow": ["spells.elements.air", "spells.elements.water"],
                "deny": ["spells.elements.fire"],
            }
        ],
    },
)


def test_compliant_project_passes(spellbook):
    result = layered_dependencies.run(RULE, spellbook)
    assert result.status == PASS
    assert result.violations == []
    assert result.scanned_files > 0


def test_offense_may_depend_on_fire(spellbook):
    """The rule is scoped to a layer, not a global ban on the word 'fire'."""
    result = layered_dependencies.run(RULE, spellbook)
    assert result.status == PASS
    fire_users = (spellbook / "src" / "spells" / "offense" / "flame_lance.py").read_text()
    assert "fire" in fire_users  # the dependency really is there


def test_absolute_fire_import_in_protection_fails(spellbook):
    target = spellbook / "src" / "spells" / "protection" / "shield.py"
    target.write_text("from spells.elements import fire\n\n\ndef cast():\n    pass\n")

    result = layered_dependencies.run(RULE, spellbook)
    assert result.status == FAIL
    assert len(result.violations) == 1
    violation = result.violations[0]
    assert violation.target_module == "spells.elements.fire"
    assert violation.source_module == "spells.protection.shield"
    assert violation.line == 1


def test_relative_fire_import_in_protection_fails(spellbook):
    """The form a path-based check would miss."""
    target = spellbook / "src" / "spells" / "protection" / "ward.py"
    target.write_text("from ..elements import fire\n\n\ndef cast():\n    pass\n")

    result = layered_dependencies.run(RULE, spellbook)
    assert result.status == FAIL
    assert result.violations[0].target_module == "spells.elements.fire"


def test_dependency_outside_the_allow_list_fails(spellbook):
    """Allow is a whitelist, not decoration: earth is neither allowed nor denied."""
    (spellbook / "src" / "spells" / "elements" / "earth.py").write_text("x = 1\n")
    (spellbook / "src" / "spells" / "protection" / "shield.py").write_text(
        "from spells.elements import earth\n"
    )

    result = layered_dependencies.run(RULE, spellbook)
    assert result.status == FAIL
    assert result.violations[0].target_module == "spells.elements.earth"
    assert "may only depend on" in result.violations[0].reason


def test_intra_layer_dependency_is_allowed(spellbook):
    (spellbook / "src" / "spells" / "protection" / "shield.py").write_text(
        "from spells.protection import ward\n"
    )
    assert layered_dependencies.run(RULE, spellbook).status == PASS


def test_missing_source_root_is_an_error_not_a_pass(tmp_path):
    """A rule that cannot run must never report green."""
    result = layered_dependencies.run(RULE, tmp_path)
    assert result.status == ERROR
    assert "does not exist" in result.error


def test_empty_source_root_is_an_error_not_a_pass(tmp_path):
    (tmp_path / "src").mkdir()
    result = layered_dependencies.run(RULE, tmp_path)
    assert result.status == ERROR
    assert result.status != PASS


def test_unparsable_file_is_an_error_not_a_pass(spellbook):
    (spellbook / "src" / "spells" / "protection" / "broken.py").write_text(
        "def cast(:\n"
    )
    result = layered_dependencies.run(RULE, spellbook)
    assert result.status == ERROR
