"""DOC-001's engine: a document that says which code it describes."""

from golden_thread_testkit import rule

from golden_thread.checks import doc_stamp
from golden_thread.docs import Target, stamp
from golden_thread.errors import GoldenThreadError
from golden_thread.results import ERROR, FAIL, PASS

import pytest


def a_rule(**overrides):
    params = {
        "document": "docs/ARCHITECTURE.md",
        "describes": "src",
        "describes_globs": ["**/*.py"],
    }
    params.update(overrides)
    return rule("DOC-001", doc_stamp.NAME, **params)


@pytest.fixture
def documented(spellbook):
    docs = spellbook / "docs"
    docs.mkdir()
    (docs / "ARCHITECTURE.md").write_text("# Spellbook\n\nProtection may not use Fire.\n")
    return spellbook


def target(project):
    return Target(a_rule(), project / "docs" / "ARCHITECTURE.md", "src")


def test_a_missing_document_fails_and_says_where_it_should_be(spellbook):
    result = doc_stamp.run(a_rule(), spellbook)
    assert result.status == FAIL
    assert any("no docs/ARCHITECTURE.md" in note for note in result.notes)


def test_an_unstamped_document_makes_no_claim_and_fails(documented):
    result = doc_stamp.run(a_rule(), documented)
    assert result.status == FAIL
    assert any("carries no golden-thread stamp" in note for note in result.notes)
    assert any("golden-thread: describes src/" in note for note in result.notes)


def test_a_stamped_document_passes(documented):
    stamp(documented, target(documented))
    result = doc_stamp.run(a_rule(), documented)
    assert result.status == PASS


def test_a_pass_still_says_what_it_does_not_prove(documented):
    """A verdict without its reason is exactly what this project refuses."""
    stamp(documented, target(documented))
    result = doc_stamp.run(a_rule(), documented)
    assert any("not a claim that the prose is correct" in n for n in result.notes)


def test_the_stamp_stops_applying_when_the_code_moves(documented):
    stamp(documented, target(documented))
    (documented / "src" / "spells" / "elements" / "air.py").write_text("x = 2\n")

    result = doc_stamp.run(a_rule(), documented)
    assert result.status == FAIL
    assert any("the code moved and the documentation did not" in n for n in result.notes)


def test_re_stamping_after_a_change_passes_again(documented):
    stamp(documented, target(documented))
    (documented / "src" / "spells" / "elements" / "air.py").write_text("x = 2\n")
    stamp(documented, target(documented))
    assert doc_stamp.run(a_rule(), documented).status == PASS


def test_a_stamp_naming_a_different_root_is_not_this_requirements_stamp(documented):
    (documented / "docs" / "ARCHITECTURE.md").write_text(
        "# Spellbook\n\n<!-- golden-thread: describes lib/ sha256:" + "a" * 64 + " -->\n"
    )
    result = doc_stamp.run(a_rule(), documented)
    assert result.status == FAIL
    assert any("claims to describe lib/" in note for note in result.notes)


def test_stamping_replaces_rather_than_accumulates(documented):
    stamp(documented, target(documented))
    (documented / "src" / "spells" / "elements" / "air.py").write_text("x = 3\n")
    stamp(documented, target(documented))
    text = (documented / "docs" / "ARCHITECTURE.md").read_text()
    assert text.count("golden-thread: describes") == 1


def test_stamping_an_unchanged_document_reports_no_change(documented):
    stamp(documented, target(documented))
    _, changed = stamp(documented, target(documented))
    assert changed is False


def test_a_document_that_does_not_exist_is_not_created_by_stamping(spellbook):
    """A file containing nothing but a digest would satisfy the letter of the
    requirement while emptying it."""
    (spellbook / "docs").mkdir()
    with pytest.raises(GoldenThreadError, match="stamp on an empty page"):
        stamp(spellbook, target(spellbook))


def test_the_subject_covers_both_the_document_and_the_code(documented):
    """Either moving means the recorded verdict no longer describes what is in
    front of us, which is what STALE is for."""
    before = doc_stamp.subject(a_rule(), documented)

    (documented / "docs" / "ARCHITECTURE.md").write_text("# Rewritten\n")
    after_doc = doc_stamp.subject(a_rule(), documented)
    assert after_doc.digest != before.digest

    (documented / "src" / "spells" / "elements" / "air.py").write_text("x = 4\n")
    after_code = doc_stamp.subject(a_rule(), documented)
    assert after_code.digest != after_doc.digest


def test_nothing_to_describe_is_error_not_failure(tmp_path):
    project = tmp_path / "empty"
    (project / "docs").mkdir(parents=True)
    (project / "docs" / "ARCHITECTURE.md").write_text("# Nothing\n")
    result = doc_stamp.run(a_rule(), project)
    assert result.status == ERROR
    assert "no code for" in result.error
