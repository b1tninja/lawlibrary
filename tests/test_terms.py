"""Each name that collides has one reading. The other reading stays on its own class."""

from apa import Code
from needles import (
    California, Cut, General, House, Insurance, PublicUtilitiesSection, Section, Session,
    breakdown, consider, cuts, members, outline,
)
from places import page
from sample import Draw
from weight import Scope, Weight, _by_common, idf_weight


def test_a_statutes_chapter_is_a_session():
    law = Session.year(2023).chapter(142)
    assert law.reference() == 'Chapter 142 of the Statutes of 2023'
    assert law.chapter == '142'
    assert outline(Code.CIVIL).order.index('chapter') >= 0


def test_a_section_of_a_session_chapter_is_the_enrolled_bill():
    law = Session.year(2023).chapter(142).section(4)
    assert law.act == '4'
    assert law.target() == '2023 142'
    assert law.reference().startswith('Section 4 of Chapter 142')


def test_an_article_identifies_only_the_constitution():
    assert outline(Code.CONSTITUTION).identifies('article')
    assert not outline(Code.CIVIL).identifies('article')


def test_the_codes_that_define_subdivision_are_opened_by_citation():
    """Each defining section is looked up. The sentence stays in the index."""
    from places import Citation
    from needles import CodeSection
    defined = (
        (Code.BUSINESS_AND_PROFESSIONS, '15'),
        (Code.CORPORATIONS, '10'),
        (Code.EVIDENCE, '7'),
        (Code.FISH_AND_GAME, '73'),
        (Code.FINANCIAL, '9'),
        (Code.GOVERNMENT, '10'),
        (Code.HARBORS_AND_NAVIGATION, '10'),
        (Code.HEALTH_AND_SAFETY, '10'),
        (Code.INSURANCE, '10'),
        (Code.PUBLIC_UTILITIES, '10'),
        (Code.REVENUE_AND_TAXATION, '10'),
        (Code.UNEMPLOYMENT_INSURANCE, '9'),
        (Code.VEHICLE, '11'),
        (Code.WATER, '10'),
        (Code.WELFARE_AND_INSTITUTIONS, '10'),
    )
    section_only = (
        (Code.EDUCATION, '71'),
        (Code.ELECTIONS, '353'),
        (Code.FOOD_AND_AGRICULTURAL, '41'),
        (Code.LABOR, '10'),
        (Code.MILITARY_AND_VETERANS, '10'),
        (Code.PUBLIC_RESOURCES, '10'),
        (Code.STREETS_AND_HIGHWAYS, '10'),
    )
    for code, number in defined:
        text = Citation(code).section(number).text
        if not text:
            return
        assert 'subdivision' in text.lower()
        assert isinstance(breakdown(code), (California, Insurance))
    insurance = Citation(Code.INSURANCE).section('10').text.lower()
    assert 'subsection' in insurance
    evidence = Citation(Code.EVIDENCE).section('7').text.lower()
    assert 'paragraph' in evidence
    for code, number in section_only:
        assert CodeSection not in consider(code)
        text = Citation(code).section(number).text
        if text:
            assert 'section' in text.lower()


def test_a_public_utilities_cut_is_a_subdivision():
    """The code that defines subdivision still parses subsection. Civil keeps both words."""
    from needles import CodeSection
    assert 'subdivision' in cuts(Code.PUBLIC_UTILITIES)
    assert 'subsection' in cuts(Code.PUBLIC_UTILITIES)
    assert PublicUtilitiesSection in consider(Code.PUBLIC_UTILITIES)
    assert Section not in consider(Code.PUBLIC_UTILITIES)
    assert CodeSection in consider(Code.GOVERNMENT)
    assert 'subsection' in cuts(Code.CIVIL)
    assert isinstance(breakdown(Code.GOVERNMENT), California)
    assert isinstance(breakdown(Code.INSURANCE), Insurance)
    assert isinstance(breakdown(Code.CIVIL), General)
    assert Cut.SUBSECTION in members(House)
    assert Cut.SUBDIVISION not in members(House)
    assert Cut.SUBDIVISION in members(California)
    assert Cut.SUBSECTION in members(Insurance)
    assert Cut.SUBSECTION not in members(California)


def test_a_page_and_line_are_a_bill_sheet():
    assert page(12).line(5).reference() == 'Page 12, line 5'
    assert page(12).line(16).through(page=15, line=11).reference().startswith('Page 12, line 16 through')


def test_choose_returns_the_sample():
    closed = Draw(Code.CIVIL).take(5).seed(1)
    assert callable(closed.choose)
    assert not hasattr(Draw, 'draw')
    assert Draw('').citations()[:1] == []


def test_common_lists_the_shared_term_and_rank_prefers_the_rare_one():
    rare = Weight(Scope.CODE, 'FGC', 'smelt', 40, 1, idf_weight(1, 29), 9.0)
    shared = Weight(Scope.CODE, 'FGC', 'shall', 400, 29, idf_weight(29, 29), 1.0)
    assert _by_common([rare, shared], 2)[0].term == 'shall'
    assert rare.score > shared.score
