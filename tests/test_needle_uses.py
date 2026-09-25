"""Uses drawn from the needle sample. The sentences come from the index."""

from apa import Code
from places import Citation

from canons import Canon, find_signals
from lexical import Clause, find_clauses
from mentions import find_mentions


def _text(code, number):
    text = Citation(code).section(number).text
    return text or None


def test_as_the_case_may_be_is_not_permission():
    text = _text(Code.PUBLIC_UTILITIES, '7578')
    if text is None or 'as the case may be' not in text.lower():
        return
    span = text.lower().find('as the case may be')
    hits = [
        signal for signal in find_signals(text, Canon.PERMISSIVE)
        if signal.start >= span and signal.start < span + len('as the case may be')
    ]
    assert hits == []


def test_a_unit_that_shall_not_apply_is_scope():
    text = _text(Code.STREETS_AND_HIGHWAYS, '31200')
    if text is None:
        return
    assert any(mark.clause is Clause.APPLICATION for mark in find_clauses(text))


def test_a_quoted_term_that_means_is_a_definition():
    text = _text(Code.UNEMPLOYMENT_INSURANCE, '13007')
    if text is None:
        return
    assert any(mark.clause is Clause.DEFINITIONS for mark in find_clauses(text))


def test_no_person_shall_is_a_prohibition():
    text = _text(Code.WATER, '13750.5')
    if text is None:
        return
    assert any(mark.clause is Clause.PROHIBITION for mark in find_clauses(text))


def test_shall_constitute_is_an_effect():
    text = _text(Code.PUBLIC_UTILITIES, '29153')
    if text is None:
        return
    assert any(mark.clause is Clause.EFFECT for mark in find_clauses(text))


def test_an_appropriation_is_marked():
    text = _text(Code.INSURANCE, '12699.525')
    if text is None:
        return
    assert any(mark.clause is Clause.APPROPRIATION for mark in find_clauses(text))


def test_liberal_construction_and_the_singular():
    chapter = _text(Code.FOOD_AND_AGRICULTURAL, '78428')
    whole = _text(Code.GOVERNMENT, '13')
    if chapter:
        assert any(mark.clause is Clause.CONSTRUCTION for mark in find_clauses(chapter))
    if whole:
        assert any(mark.clause is Clause.CONSTRUCTION for mark in find_clauses(whole))


def test_the_whole_chapter_falling_is_not_severability():
    text = _text(Code.GOVERNMENT, '77400')
    if text is None:
        return
    kinds = {mark.clause for mark in find_clauses(text)}
    assert Clause.NONSEVERABILITY in kinds
    assert Clause.SEVERABILITY not in kinds


def test_a_code_wide_savings_clause_names_this_code():
    text = _text(Code.EDUCATION, '6')
    if text is None:
        return
    assert any(mark.clause is Clause.SEVERABILITY for mark in find_clauses(text))


def test_may_be_cited_as_is_a_short_title():
    text = _text(Code.WELFARE_AND_INSTITUTIONS, '11200')
    if text is None:
        return
    assert any(mark.clause is Clause.SHORT_TITLE for mark in find_clauses(text))


def test_a_county_auditor_is_an_office():
    text = _text(Code.WATER, '70237')
    if text is None:
        return
    assert any(mention.name == 'county auditor' for mention in find_mentions(text))
