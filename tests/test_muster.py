from apa import Code, parse

from drafting import Body, Level, SOURCES, level
from muster import Expectation, muster
from structure import Rank
from structure import find_links
import query


def test_a_letter_is_a_subdivision():
    assert level(Rank.LETTER) is Level.SUBDIVISION
    assert level(Rank.NUMBER) is Level.PARAGRAPH
    assert level(Rank.CAPITAL) is Level.SUBPARAGRAPH
    assert level(Rank.CLAUSE) is Level.CLAUSE
    assert any(source.body is Body.LEGISLATIVE and 'legcounsel.house.gov' in source.url for source in SOURCES)
    assert any(source.body is Body.ACADEMIC for source in SOURCES)


def test_a_skipped_letter_is_a_fault():
    faults = muster('(a) One.\n(c) Three.')
    assert any(fault.expectation is Expectation.SEQUENCE and fault.label == '(c)' for fault in faults)


def test_a_named_subdivision_that_is_missing_is_a_fault():
    faults = muster('(a) Except as provided in subdivision (b), this section applies.')
    assert any(fault.expectation is Expectation.LOCAL_LABEL and fault.label == '(b)' for fault in faults)


def test_a_following_list_without_items_is_a_fault():
    faults = muster('(b) Either of the following applies here.')
    assert any(fault.expectation is Expectation.FOLLOWING for fault in faults)


def test_civil_code_section_1940_meets_the_sequence():
    ref = parse('Civil Code section 1940')
    doc = query.section(ref.code, ref.span.numbers[0])
    if not doc.get('found'):
        return
    faults = [fault for fault in muster(doc['text']) if fault.expectation is Expectation.SEQUENCE]
    assert faults == []
    assert any(link.section == '7280' and link.code is Code.REVENUE_AND_TAXATION for link in find_links(doc['text'], here=ref.code))
