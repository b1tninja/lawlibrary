"""Structural customary clauses. The sentence is the indexed section, sliced to the phrase."""

from apa import Code
from lexical import Clause, find_clauses
from places import Citation


def _marked(code, number, phrase, kind):
    text = Citation(code).section(number).containing(phrase)
    if not text:
        return
    assert kind in {mark.clause for mark in find_clauses(text)}


def test_enacting_clause():
    """GOV 9501.5. The people of the State of California do enact as follows."""
    _marked(Code.GOVERNMENT, '9501.5', 'do enact as follows', Clause.ENACTMENT)


def test_short_title():
    """GOV 1. This act shall be known as the Government Code."""
    _marked(Code.GOVERNMENT, '1', 'shall be known as', Clause.SHORT_TITLE)


def test_long_title():
    """EDC 92141. An act to provide for cooperative agricultural extension work."""
    _marked(Code.EDUCATION, '92141', 'Smith-Lever', Clause.LONG_TITLE)


def test_purpose_whereas():
    """EDC 300. Whereas clauses state the purpose of the measure."""
    _marked(Code.EDUCATION, '300', 'Whereas', Clause.PURPOSE)


def test_findings():
    """HSC 50009. The Legislature finds and declares."""
    _marked(Code.HEALTH_AND_SAFETY, '50009', 'finds and declares', Clause.FINDINGS)


def test_definitions():
    """CIV 1997.020. As used in this chapter."""
    _marked(Code.CIVIL, '1997.020', 'As used in this chapter', Clause.DEFINITIONS)


def test_proviso():
    """CIV 1798.79.9. Provided that collection does not identify any individual."""
    _marked(Code.CIVIL, '1798.79.9', 'provided that', Clause.PROVISO)


def test_exception():
    """EVID 1228.1. Except as provided in subdivision (b)."""
    _marked(Code.EVIDENCE, '1228.1', 'Except as provided', Clause.EXCEPTION)


def test_savings():
    """FAM 2128. Nothing in this chapter affects the rights of a bona fide purchaser."""
    _marked(Code.FAMILY, '2128', 'bona fide', Clause.SAVINGS)


def test_severability():
    """GOV 7492. If any provision of this chapter is held invalid."""
    _marked(Code.GOVERNMENT, '7492', 'held invalid', Clause.SEVERABILITY)


def test_effective_date():
    """BPC 11288. This chapter shall take effect on July 1, 2005."""
    _marked(Code.BUSINESS_AND_PROFESSIONS, '11288', 'shall take effect', Clause.EFFECTIVE_DATE)


def test_sunset():
    """FAC 19220. A license granted under this chapter shall expire on December 31."""
    _marked(Code.FOOD_AND_AGRICULTURAL, '19220', 'shall expire', Clause.SUNSET)


def test_repealer():
    """WAT 38500. Chapter 387 of the Statutes of 1913 is hereby repealed."""
    _marked(Code.WATER, '38500', 'hereby repealed', Clause.REPEALER)
