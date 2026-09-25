from lexical import Clause, find_clause, find_clauses


ENACTED = """
Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled, That this Act shall be known as the Sample Act.
This Act shall take effect on January 1.
The office acts pursuant to section 10050.
For purposes of this Act, the word office means the department.
If any provision of this Act is held invalid, the rest remains.
"""


def test_enactment_clause_is_marked():
    marks = find_clause(ENACTED, Clause.ENACTMENT)
    assert len(marks) == 1
    assert marks[0].text.lower().startswith('be it enacted')
    assert marks[0].clause.value == 'enactment'


def test_california_style_enacting_words():
    text = 'The people of the State of California do enact as follows:'
    marks = find_clause(text, Clause.ENACTMENT)
    assert len(marks) == 1


def test_an_ordinance_ordains():
    """The rare enacting clauses. A city or district ordinance ordains."""
    for words in ('do ordain as follows', 'does ordain as follows'):
        marks = find_clause('The board %s.' % words, Clause.ENACTMENT)
        assert len(marks) == 1
        assert words in marks[0].text.lower()


def test_customary_clauses_are_all_found():
    kinds = {mark.clause for mark in find_clauses(ENACTED)}
    assert kinds == {
        Clause.ENACTMENT,
        Clause.SHORT_TITLE,
        Clause.DEFINITIONS,
        Clause.SEVERABILITY,
        Clause.EFFECTIVE_DATE,
        Clause.AUTHORITY,
    }


def test_empty_text_has_no_marks():
    assert find_clauses('') == []
    assert find_clauses('The board shall meet.') == []


SKELETON = """
An Act to amend the sample code relating to offices.
Whereas a record should be kept; now, therefore.
The Legislature finds and declares that a department is needed.
The purpose of this Act is to name that department.
A permit shall issue, provided that the fee is paid, except as the board waives it.
Nothing in this Act affects any proceeding commenced before the effective date.
Section 12 is hereby repealed.
This chapter remains in effect until December 31 and as of that date is repealed.
"""


def test_structural_clauses_are_marked():
    kinds = {mark.clause for mark in find_clauses(SKELETON)}
    assert Clause.LONG_TITLE in kinds
    assert Clause.PURPOSE in kinds
    assert Clause.FINDINGS in kinds
    assert Clause.PROVISO in kinds
    assert Clause.EXCEPTION in kinds
    assert Clause.SAVINGS in kinds
    assert Clause.REPEALER in kinds
    assert Clause.SUNSET in kinds
