"""A nested reference keeps the unit it was opened inside."""

from apa import Code
from places import Citation, book, division, line, page, subchapter


def test_a_paragraph_closes_over_the_division_and_the_code():
    """Chapter 2 of Part 1 of Division 4, then the section and its paragraph."""
    with book(Code.BUSINESS_AND_PROFESSIONS) as bpc:
        ref = (
            bpc.division(4).part(1).chapter(2, commencing='10050')
            .section('10050').subdivision('a').paragraph(1)
        )
    assert ref.reference() == (
        'paragraph (1) of subdivision (a) of Section 10050 of '
        'Chapter 2 (commencing with Section 10050) of Part 1 of Division 4 of '
        'the Business and Professions Code'
    )


def test_a_with_block_is_the_parent_the_next_call_closes_over():
    """Inside a division, part(1) is that division's part."""
    with book(Code.GOVERNMENT):
        with division(3):
            ref = subchapter(1)
    assert ref.reference() == 'Subchapter 1 of Division 3 of the Government Code'


def test_a_selector_reads_the_section_and_finds_inside_the_division():
    """BPC 10050 is opened by citation. The hunt stays inside Division 4."""
    opened = book(Code.BUSINESS_AND_PROFESSIONS).section('10050').read()
    if not opened.get('found'):
        return
    assert opened.get('code') == 'BPC'
    assert opened.get('section') == '10050'
    hits = book(Code.BUSINESS_AND_PROFESSIONS).division(4).find('Real Estate Commissioner', limit=5)
    assert any(hit.get('section') == '10050' for hit in hits)


def test_a_call_stacks_labels_and_a_pair_is_siblings():
    """section('4600')('a')(1) is the nest. ('a', 'b') is the series."""
    nest = Citation(Code.CIVIL).section('4600')('a')(1)
    assert nest.reference() == 'Civil Code section 4600, subdivision (a), paragraph (1)'
    series = Citation(Code.CIVIL).section('4600')('a', 'b')
    assert series.reference() == 'Civil Code section 4600, subdivisions (a) and (b)'


def test_a_citation_prints_the_code_section_and_subdivision():
    """Civil Code section 4600, subdivision (b), without pasting the sentence."""
    cited = Citation(Code.CIVIL).section(4600).subdivision('b')
    assert cited.reference() == 'Civil Code section 4600, subdivision (b)'
    assert str(cited) == cited.reference()


def test_a_citation_slices_the_stored_subdivision():
    """GOV 12802. Subdivision (a) is the stored words under that label."""
    cited = Citation(Code.GOVERNMENT).section('12802').subdivision('a')
    assert cited.reference() == 'Government Code section 12802, subdivision (a)'
    if not cited.text:
        return
    assert 'Natural Resources Agency' in cited.text
    assert 'Natural' in cited.words()
    assert '(a)' in Citation(Code.GOVERNMENT).section('12802').subdivisions


def test_a_range_a_series_and_an_open_end_print_and_parse():
    """The printed span is the same chain the parser rebuilds."""
    from apa import parse
    from citations import Cite
    ranged = Citation(Code.CIVIL).section('1119').through('1124')
    assert ranged.reference() == 'Civil Code sections 1119 to 1124'
    assert parse(ranged.reference()).span.cite is Cite.RANGE
    series = Citation(Code.GOVERNMENT).section('12926').and_('12926.1')
    assert series.reference() == 'Government Code sections 12926 and 12926.1'
    assert parse(series.reference()).span.numbers == ('12926', '12926.1')
    opened = Citation(Code.GOVERNMENT).section('11340').commencing()
    assert opened.reference() == 'Government Code, commencing with Section 11340'
    assert parse(opened.reference()).span.open is True
    article = Citation(Code.CONSTITUTION).article('XIII A').section('4')
    assert article.reference() == 'California Constitution, article XIII A, section 4'
    parsed = parse(article.reference())
    assert parsed.article.value == 'XIII A'
    assert parsed.span.subdivision is None
    headed = Citation(Code.CIVIL).article('1').section('1940')
    assert headed.reference() == 'Civil Code section 1940'


def test_a_citation_walk_closes_over_the_hops_and_the_books():
    """The visited set is built when the diagram is drawn, not on the chain."""
    cited = Citation(Code.CIVIL).section('1940').hops(0).only(
        Code.CIVIL, Code.REVENUE_AND_TAXATION,
    ).same()
    assert cited.hops_depth == 0
    assert cited.same_book is True
    chart = cited.diagram()
    if not chart:
        return
    assert 'CIV1940' in chart
    assert '-->' not in chart
    node = Citation(Code.CIVIL).section('1714.1').refs
    opened = node.follow()
    assert opened
    assert len({child.key for child in opened}) == len(opened)
    assert node.follow() == []
    cited = Citation(Code.CIVIL).section('1714.1').hops(1)
    assert cited.refs is cited.refs
    assert '```mermaid' in cited.md
    assert cited.chart.startswith('flowchart')
    assert cited.refs.md == cited.md
    node = cited.refs
    assert node.chart is node.chart
    assert node.md == cited.md
    fish = Citation(Code.FISH_AND_GAME).section('8681.5').hops(0).refs
    if fish.tree.get('found'):
        assert fish.sessions
        assert all(len(row.split()) == 2 for row in fish.sessions)


def test_a_bill_cites_the_page_and_the_line():
    """Page and line are the only span that uses keywords."""
    assert page(12).line(5).reference() == 'Page 12, line 5'
    span = page(12).line(16).through(page=15, line=11)
    assert span.reference() == 'Page 12, line 16 through page 15, line 11'
    cited = Citation(Code.CIVIL).page(12).line(16).through(page=15, line=11)
    assert cited.reference() == 'Page 12, line 16 through page 15, line 11'


def test_a_citation_keeps_the_session_it_was_opened_in():
    """The year closed over is the publication that is read. Another year is a miss."""
    from structure import related

    prior = Citation(Code.BUSINESS_AND_PROFESSIONS).section('11500').session('2011')
    assert prior.session_year == '2011'
    assert prior.text
    assert Citation(Code.BUSINESS_AND_PROFESSIONS).session('2011').section('11500').text
    current = prior.session('2025')
    assert current.text == ''
    assert current.words() == []
    assert current.place.read(session='2025')['reason'] == 'not_in_index'
    walk = related(Code.BUSINESS_AND_PROFESSIONS, '11500', depth=1, session='2011')
    assert walk.get('found') is True
    assert related(Code.BUSINESS_AND_PROFESSIONS, '11500', session='2025').get('found') is False


def test_a_line_is_a_mark_inside_the_open_section():
    """A bill line is named in parentheses, under the section that is open."""
    with book(Code.GOVERNMENT):
        ref = line(12)
    assert ref.reference().startswith('line (12) of the Government Code')
