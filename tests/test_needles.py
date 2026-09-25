"""Word classes are registered once. A book supplies a reading only for itself."""

from apa import Code
from needles import (
    AgencyNoun, Article, Bill, Board, ConstitutionOutline, Department, JointBill, Noun,
    Outline, PublicUtilitiesSection, Section, Session, consider, nouns, outline,
)
from parsers import JointRules, PublicUtilities


def test_department_agency_and_board_are_noun_classes():
    """The office titles are one registry. A hunter enumerates it."""
    assert issubclass(Department, Noun)
    assert issubclass(AgencyNoun, Noun)
    assert issubclass(Board, Noun)
    titles = {cls.__name__ for cls in nouns()}
    assert {'Department', 'AgencyNoun', 'Board', 'Commission', 'Secretary', 'Council', 'Authority', 'Conservancy'} <= titles
    assert Department in nouns()
    assert AgencyNoun in nouns()
    assert Board in nouns()


def test_an_article_identifies_a_constitution_section_and_heads_a_code():
    """The same word is a different unit. The book says which."""
    code = outline(Code.CIVIL)
    charter = outline(Code.CONSTITUTION)
    assert isinstance(code, Outline)
    assert isinstance(charter, ConstitutionOutline)
    assert code.order.index('chapter') < code.order.index('article')
    assert charter.order == ('article', 'section')
    assert charter.identifies('article')
    assert not code.identifies('article')
    assert code.mark == 'subdivision'
    assert Session.order == ('year', 'chapter')
    law = Session.year(1913).chapter(387)
    assert law.reference() == 'Chapter 387 of the Statutes of 1913'
    assert law.section(1).reference() == 'Section 1 of Chapter 387 of the Statutes of 1913'
    assert law.target() == '1913 387'


def test_section_article_and_bill_are_word_classes():
    assert issubclass(Section, object)
    assert issubclass(Article, Section.__bases__[0])
    assert issubclass(Bill, Article.__bases__[0])
    general = consider()
    assert Section in general
    assert Article in general
    assert Bill in general
    assert JointBill not in general
    assert PublicUtilitiesSection not in general


def test_a_code_replaces_the_general_reading():
    utilities = {cls.__name__ for cls in PublicUtilities().words()}
    assert 'PublicUtilitiesSection' in utilities
    assert 'Section' not in utilities
    civil = {cls.__name__ for cls in consider(Code.CIVIL)}
    assert 'Section' in civil
    assert 'PublicUtilitiesSection' not in civil


def test_joint_rules_replace_the_general_bill():
    rules = {cls.__name__ for cls in JointRules().words()}
    assert 'JointBill' in rules
    assert 'Bill' not in rules
    assert JointBill.reading != Bill.reading
