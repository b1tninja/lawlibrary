import pytest

from apa import CitationSystem, Code, active, cite, section, series, span
from citations import Cite
from government import Article
from parsers import Guide


def test_a_code_member_carries_its_token_and_shorthand():
    assert Code.BUSINESS_AND_PROFESSIONS.value == 'BPC'
    assert Code.BUSINESS_AND_PROFESSIONS.shorthand == 'Bus. & Prof. Code'
    assert Code.CIVIL.title == 'Civil Code'
    assert Code.get('CIV') is Code.CIVIL


def test_one_section_is_a_reference_and_two_in_text_forms():
    ref = cite(Code.BUSINESS_AND_PROFESSIONS, section('10050', 'd'), session='2025')
    assert ref.span.cite is Cite.SECTION
    assert ref.index() == 'BPC 10050'
    assert ref.reference() == 'Business and Professions Code section 10050, subdivision (d)'
    assert ref.guide is Guide.CALIFORNIA_STYLE_MANUAL
    assert ref.parenthetical() == '(Business and Professions Code, 2025)'
    assert ref.narrative() == 'Business and Professions Code (2025)'


def test_a_range_and_a_series_use_the_double_sign():
    ranged = cite(Code.CIVIL, span('4000', '6150'))
    assert ranged.reference() == 'Civil Code sections 4000 to 6150'
    listed = cite(Code.GOVERNMENT, series('11340', '11370'), session='2011')
    assert listed.span.cite is Cite.SERIES
    assert listed.reference() == 'Government Code sections 11340 and 11370'


def test_a_constitution_article_sits_beside_the_section():
    ref = cite(Code.CONSTITUTION, section('1'), article=Article.VI)
    assert ref.reference() == 'California Constitution, article VI, section 1'


def test_a_with_block_selects_the_citation_system():
    assert active() is None
    with CitationSystem.CaliforniaStyleManual:
        filed = cite(Code.CIVIL, section('1940'))
        assert filed.guide is Guide.CALIFORNIA_STYLE_MANUAL
        assert filed.reference() == 'Civil Code section 1940'
        with CitationSystem.APA:
            listed = cite(Code.CIVIL, section('1940'), session='2025')
            assert listed.guide is Guide.APA
            assert listed.reference().startswith('Civil Code,')
        assert active() is Guide.CALIFORNIA_STYLE_MANUAL
    assert active() is None


def test_a_bare_number_is_not_a_span():
    with pytest.raises(TypeError):
        cite(Code.CIVIL, 1940)
