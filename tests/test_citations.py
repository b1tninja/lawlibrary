from citations import Cite, find_citations


PROSE = """
See Bus. & Prof. Code § 10050.
The duties run through §§ 10050-10080.
Cf. Gov. Code §§ 11340, 11370.
Civil Code section 5806(a) is one section.
"""


def test_single_sign_is_one_section():
    points = [point for point in find_citations(PROSE) if point.cite is Cite.SECTION and '10050' in point.numbers]
    assert points
    assert points[0].numbers == ('10050',)
    assert points[0].signal == 'see'
    assert '§§' not in points[0].text


def test_double_sign_is_a_range_or_a_series():
    points = find_citations(PROSE)
    ranged = next(point for point in points if point.cite is Cite.RANGE)
    series = next(point for point in points if point.cite is Cite.SERIES)
    assert ranged.numbers == ('10050', '10080')
    assert series.numbers == ('11340', '11370')
    assert series.signal == 'cf'


def test_a_semicolon_keeps_the_series():
    """A semicolon separates the same series a comma does."""
    from structure import find_links
    from apa import Code
    points = find_citations('Section 51; 54; 54.1; or 55.')
    assert points[0].cite is Cite.SERIES
    assert points[0].numbers == ('51', '54', '54.1', '55')
    links = find_links('Section 51; 54; or 55.', here=Code.CIVIL)
    assert [link.section for link in links if link.kind == 'statute'] == ['51', '54', '55']


def test_a_conjunction_or_a_disjunction_is_an_iterable_series():
    """Each joined section is one item. The join stays on the series."""
    from citations import Join, Note, annotate
    disjunction = find_citations('Section 51; 54; or 55.')[0]
    assert disjunction.cite is Cite.SERIES
    assert disjunction.join is Join.DISJUNCTION
    assert [item.numbers for item in disjunction] == [('51',), ('54',), ('55',)]
    assert [item.cite for item in disjunction] == [Cite.SECTION, Cite.SECTION, Cite.SECTION]
    conjunction = find_citations('Sections 51, 54, and 55.')[0]
    assert conjunction.join is Join.CONJUNCTION
    both = find_citations('Section 51, 54, and/or 55.')[0]
    assert both.join is Join.BOTH
    notes = [note for note in annotate('Section 51, 54, or 55.') if note.note is Note.CITATION]
    assert [note.text for note in notes] == ['51', '54', '55']
    assert {note.cite for note in notes} == {Cite.SERIES}
    assert {note.join for note in notes} == {Join.DISJUNCTION}


def test_and_or_keeps_every_number_and_both_readings():
    """', and/or' is one join. The series keeps every number. Both readings stay."""
    from canons import Canon, ambiguities
    points = find_citations('Section 51, 54, and/or 55.')
    assert points[0].cite is Cite.SERIES
    assert points[0].numbers == ('51', '54', '55')
    found = ambiguities('Submit the form, the fee, and/or the waiver.')
    assert any(
        {item.left.canon, item.right.canon} == {Canon.CONJUNCTION, Canon.DISJUNCTION}
        for item in found
    )


def test_a_series_keeps_the_last_number_after_or():
    """CIV 55.51. The last number after ', or' stays in the series."""
    from apa import Code
    from places import Citation
    from structure import find_links
    text = Citation(Code.CIVIL).section('55.51').text
    if not text:
        return
    series = [point for point in find_citations(text) if point.cite is Cite.SERIES]
    assert any(point.numbers == ('51', '54', '54.1', '55') for point in series)
    links = find_links(text, here=Code.CIVIL)
    assert any(link.kind == 'statute' and link.section == '55' for link in links)


def test_words_before_section_are_not_a_code():
    point = find_citations('YEAR PERIOD PROVIDED IN SECTION 16460')[0]
    assert point.numbers == ('16460',)
    assert not point.code
    from query import section
    doc = section('PROB', '16461')
    assert doc['found']
    points = find_citations(doc['text'])
    assert any('16460' in point.numbers for point in points)
    assert all('PERIOD' not in (point.code or '') for point in points)


def test_spelled_section_is_the_same_frame():
    point = next(point for point in find_citations(PROSE) if '5806' in point.numbers)
    assert point.cite is Cite.SECTION
    assert point.numbers == ('5806',)
    assert find_citations('') == []
    assert find_citations('The board shall meet.') == []
