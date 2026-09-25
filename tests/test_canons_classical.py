"""Classical canons. Each sentence is sliced from the cited section."""

import query
from apa import Code
from canons import Canon, find_signals, readings


def _open(code, number):
    return query.section(code, number).get('text') or ''


def test_literal_shall_and_golden_proviso_differ_on_pit_privy():
    """HSC 5416. Shall states the rule. The proviso qualifies a pit privy."""
    text = _open(Code.HEALTH_AND_SAFETY, '5416')
    if 'pit privy' not in text.casefold():
        return
    assert find_signals(text, Canon.MANDATORY)
    assert find_signals(text, Canon.PROVISO)
    assert Canon.MANDATORY in readings(text)
    assert Canon.PROVISO in readings(text)
    mandatory = find_signals(text, Canon.MANDATORY)[0]
    proviso = find_signals(text, Canon.PROVISO)[0]
    assert mandatory.reading != proviso.reading


def test_funding_shall_and_proviso_are_different_readings():
    """WIC 5894. Shall directs distribution. The proviso stops a reading that reduces categories."""
    text = query.excerpt(Code.WELFARE_AND_INSTITUTIONS, '5894', 'provided, however')
    if not text:
        return
    assert find_signals(text, Canon.MANDATORY)
    assert find_signals(text, Canon.PROVISO)
    mandatory = find_signals(text, Canon.MANDATORY)[0]
    proviso = find_signals(text, Canon.PROVISO)[0]
    assert mandatory.reading != proviso.reading


def test_purpose_finds_and_declares_states_redevelopment_end():
    """HSC 33071. Finds and declares a fundamental purpose of redevelopment."""
    text = query.excerpt(Code.HEALTH_AND_SAFETY, '33071', 'fundamental purpose of redevelopment')
    if not text:
        return
    assert 'finds and declares' in text.casefold()


def test_notwithstanding_marks_specific_over_general():
    """PROB 3612. Notwithstanding any other provision marks a specific rule."""
    text = query.excerpt(Code.PROBATE, '3612', 'Notwithstanding any other provision')
    if not text:
        return
    assert find_signals(text, Canon.SPECIFIC)
    assert find_signals(text, Canon.EXCEPTION)


def test_specific_statute_prevails_over_general_provision():
    """CORP 18060. The specific statute prevails to the extent of the inconsistency."""
    text = query.excerpt(Code.CORPORATIONS, '18060', 'specific statute prevails')
    if not text:
        return
    assert 'general provision' in text.casefold()


def test_later_enacted_statute_prevails_over_earlier():
    """GOV 9605. The statute enacted last is intended to prevail over earlier ones."""
    text = _open(Code.GOVERNMENT, '9605')
    if 'enacted last' not in text.casefold():
        return
    assert find_signals(text, Canon.MANDATORY)


def test_regulations_yield_where_chapter_speaks():
    """BPC 19563. Rules and regulations may be adopted not inconsistent with this chapter."""
    text = query.excerpt(Code.BUSINESS_AND_PROFESSIONS, '19563', 'not inconsistent with this chapter')
    if not text:
        return
    assert find_signals(text, Canon.PERMISSIVE)


def test_former_and_latter_pair_precedent_and_subsequent():
    """CIV 708. Precedent and subsequent pair with beginning and ending."""
    text = _open(Code.CIVIL, '708')
    if 'precedent or subsequent' not in text.casefold():
        return
    assert 'the former' in text.casefold()
    assert 'the latter' in text.casefold()
