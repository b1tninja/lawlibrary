import pytest

from apa import CitationSystem, Code, cite, parse, section, series, span
from citations import Cite
from government import Article
from parsers import Guide
from styles import identify
from styles_chicago import Ibid
from styles_universal import NeutralCase


COURT = """
Code of Civil Procedure section 1011
Family Code section 3461
California Constitution, article VI, section 1
"""


def test_the_default_system_is_the_california_court_form():
    ref = cite(Code.CIVIL_PROCEDURE, section('1011'))
    assert ref.guide is Guide.CALIFORNIA_STYLE_MANUAL
    assert ref.reference() == 'Code of Civil Procedure section 1011'
    assert identify(ref.reference()) is CitationSystem.CaliforniaStyleManual


def test_a_rendered_citation_parses_back_to_the_same_code_and_span():
    original = cite(Code.BUSINESS_AND_PROFESSIONS, section('10050', 'd'), session='2025')
    found = parse(original.reference())
    assert found.code is Code.BUSINESS_AND_PROFESSIONS
    assert found.span.cite is Cite.SECTION
    assert found.span.numbers == ('10050',)
    assert found.span.subdivision == 'd'
    assert found.reference() == original.reference()


def test_the_court_appendix_forms_parse():
    lines = [line.strip() for line in COURT.strip().splitlines()]
    procedure, family, constitution = [parse(line) for line in lines]
    assert procedure.code is Code.CIVIL_PROCEDURE
    assert procedure.span.numbers == ('1011',)
    assert family.code is Code.FAMILY
    assert family.span.numbers == ('3461',)
    assert constitution.code is Code.CONSTITUTION
    assert constitution.article is Article.VI
    assert constitution.reference() == 'California Constitution, article VI, section 1'


def test_shorthand_signs_tokens_ranges_and_series_parse():
    assert parse('Bus. & Prof. Code, § 10050').index() == 'BPC 10050'
    assert parse('Civ. Code §§ 4000-6150').span.cite is Cite.RANGE
    assert parse('Gov. Code §§ 11340 and 11370').span.cite is Cite.SERIES
    assert parse('BPC 10050').reference() == 'Business and Professions Code section 10050'
    assert parse('Civil Code sections 4000 to 6150').span.numbers == ('4000', '6150')
    assert parse('Civil Code sections 2953.1 through 2953.4').span.cite is Cite.RANGE
    assert parse('Government Code, commencing with Section 11340').span.open is True
    assert parse('Government Code section 11340 et seq.').span.open is True
    assert parse('Government Code section 11340 et seq.').reference() == (
        'Government Code, commencing with Section 11340'
    )
    constitution = parse('California Constitution, article XIII A, section 4')
    assert constitution.article.value == 'XIII A'
    assert constitution.span.numbers == ('4',)
    assert constitution.reference() == 'California Constitution, article XIII A, section 4'
    listed = cite(Code.GOVERNMENT, series('11340', '11370', '11500'))
    assert listed.reference() == 'Government Code sections 11340, 11370, and 11500'
    assert parse(listed.reference()).span.numbers == ('11340', '11370', '11500')


def test_a_subdivision_word_and_an_attached_letter_both_parse():
    word = parse('Civil Code section 1940, subdivision (a)')
    mark = parse('Civ. Code § 1940(a)')
    assert word.span.subdivision == 'a'
    assert mark.span.subdivision == 'a'
    assert word.index() == mark.index() == 'CIV 1940'


def test_the_text_picks_another_system_when_it_carries_that_signal():
    apa = 'Civil Code, Civ. Code § 1940 (2025).'
    assert identify(apa) is CitationSystem.APA
    assert parse(apa).guide is Guide.APA
    assert parse(apa).reference() == apa
    assert identify('Cal. Civ. Code § 1940') is CitationSystem.Bluebook
    assert parse('Cal. Civ. Code § 1940').reference() == 'Cal. Civ. Code § 1940'
    assert identify('Id. at 5') is CitationSystem.Bluebook
    assert identify('Indigo Book') is CitationSystem.IndigoBook
    assert identify('per ALWD') is CitationSystem.ALWD
    assert identify('Ibid.') is CitationSystem.Chicago
    assert isinstance(parse('Ibid.'), Ibid)
    assert identify('2020 CA 5') is CitationSystem.Universal
    case = parse('2020 CA 5')
    assert isinstance(case, NeutralCase)
    assert case.reference() == '2020 CA 5'
    assert parse('BPC § 10050').guide is Guide.CALIFORNIA_STYLE_MANUAL


def test_a_with_block_forces_the_system_even_when_the_words_look_californian():
    with CitationSystem.ALWD:
        found = parse('Civ. Code § 1940')
    assert found.guide is Guide.ALWD
    assert found.reference() == 'Civ. Code § 1940'


def test_an_unknown_book_is_rejected():
    with pytest.raises(ValueError):
        parse('Not A Code section 1')
