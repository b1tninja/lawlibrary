"""Find customary clauses in statute text.

The words are already plain text. This module marks the phrases drafters
repeat: an enacting clause, a short title, a definition, a severability
clause, an effective date, and a sentence that names the statute under
which an office acts. A grammar parser can come later. These patterns are
the first pass.
"""

import enum
import re


class Clause(enum.Enum):
    """A customary span. The value is the string stored on an annotation."""

    ENACTMENT = 'enactment'
    SHORT_TITLE = 'short_title'
    DEFINITIONS = 'definitions'
    SEVERABILITY = 'severability'
    EFFECTIVE_DATE = 'effective_date'
    AUTHORITY = 'authority'
    LONG_TITLE = 'long_title'
    PURPOSE = 'purpose'
    FINDINGS = 'findings'
    PROVISO = 'proviso'
    EXCEPTION = 'exception'
    SAVINGS = 'savings'
    SUNSET = 'sunset'
    REPEALER = 'repealer'
    APPLICATION = 'application'
    EFFECT = 'effect'
    PROHIBITION = 'prohibition'
    APPROPRIATION = 'appropriation'
    CONSTRUCTION = 'construction'
    NONSEVERABILITY = 'nonseverability'


class Mark:
    """One span of a clause inside a text."""

    def __init__(self, clause, start, end, text):
        self.clause = clause
        self.start = start
        self.end = end
        self.text = text

    def __eq__(self, other):
        return (
            isinstance(other, Mark)
            and self.clause is other.clause
            and self.start == other.start
            and self.end == other.end
            and self.text == other.text
        )

    def __repr__(self):
        return 'Mark(%s, %s, %s)' % (self.clause.value, self.start, self.end)


_PATTERNS = (
    (Clause.ENACTMENT, re.compile(
        r'(?i)\b(?:be it enacted\b[^\n.]{0,240}|the people of the state of [a-z ]+ do enact as follows'
        r'|do ordain as follows|does ordain as follows)\b',
    )),
    (Clause.SHORT_TITLE, re.compile(
        r'(?i)\bthis (?:act|chapter|part|title|article|division|code) '
        r'(?:shall be known and may be cited as|may be cited as|shall be known as|may be known as|is known as)\b'
        r'[^\n.]{0,160}',
    )),
    (Clause.DEFINITIONS, re.compile(
        r'(?i)\b(?:for purposes of this|as used in this|the following definitions apply|has the same meaning as)\b[^\n.]{0,80}'
        r'|["“][^"”\n]{1,80}["”]\s+means\b',
    )),
    (Clause.SEVERABILITY, re.compile(
        r'(?i)\bif any provision of this (?:act|chapter|part|title|code|division|section|article)\b'
        r'[^\n.]{0,200}\b(?:invalid|unconstitutional)\b',
    )),
    (Clause.EFFECTIVE_DATE, re.compile(
        r'(?i)\bthis (?:act|chapter|part|section) (?:shall take effect|takes effect|becomes effective)\b[^\n.]{0,80}',
    )),
    (Clause.AUTHORITY, re.compile(
        r'(?i)\b(?:pursuant to|under the authority of|as authorized by|under section)\s+'
        r'(?:[A-Z][A-Za-z .]{0,40}\s+)?(?:section\s+)?\d[\d.]*(?:\([a-z0-9]+\))?',
    )),
    (Clause.LONG_TITLE, re.compile(
        r'(?i)\ban act to\b[^\n.]{0,200}',
    )),
    (Clause.PURPOSE, re.compile(
        r'(?i)\b(?:whereas\b[^\n.]{0,160}|the purpose of this (?:act|chapter|part) is\b[^\n.]{0,160})',
    )),
    (Clause.FINDINGS, re.compile(
        r'(?i)\b(?:the legislature|congress|the people) finds and declares\b[^\n.]{0,160}',
    )),
    (Clause.PROVISO, re.compile(
        r'(?i)\bprovided,? however, that\b|\bprovided that\b',
    )),
    (Clause.EXCEPTION, re.compile(
        r'(?i)\b(?:except that|except as|unless otherwise)\b',
    )),
    (Clause.SAVINGS, re.compile(
        r'(?i)\b(?:nothing in this (?:act|chapter|part) affects\b[^\n.]{0,120}|does not affect (?:any |the )?(?:right|rights|proceeding)\b[^\n.]{0,80})',
    )),
    (Clause.APPLICATION, re.compile(
        r'(?i)\bthis (?:section|article|chapter|part|title|division|code) shall (?:not )?apply\b',
    )),
    (Clause.EFFECT, re.compile(
        r'(?i)\bshall constitute\b|\bshall be void\b',
    )),
    (Clause.PROHIBITION, re.compile(
        r'(?i)\bno (?:person|persons|claim|claims) shall\b',
    )),
    (Clause.SUNSET, re.compile(
        r'(?i)\b(?:is repealed on|shall expire|remains in effect until|shall become inoperative on)\b[^\n.]{0,80}',
    )),
    (Clause.APPROPRIATION, re.compile(
        r'(?i)\b(?:is hereby appropriated|are hereby appropriated|authorized to be appropriated)\b',
    )),
    (Clause.CONSTRUCTION, re.compile(
        r'(?i)\bshall be liberally construed\b|\bsingular number includes the plural\b|\brules of construction\b',
    )),
    (Clause.NONSEVERABILITY, re.compile(
        r'(?i)\bif any (?:provision|portion) of this\b[^\n.]{0,180}\b(?:unconstitutional|void|invalid)\b'
        r'[^\n.]{0,180}\bentire\b[^\n.]{0,80}\binoperative\b',
    )),
    (Clause.REPEALER, re.compile(
        r'(?i)\b(?:is hereby repealed|are hereby repealed|parts of acts inconsistent with this act are repealed)\b',
    )),
)


def find_clauses(text):
    """Return every customary clause in ``text``, in order of appearance."""
    if not text:
        return []
    found = []
    for clause, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            found.append(Mark(clause, match.start(), match.end(), match.group(0)))
    found.sort(key=lambda mark: (mark.start, mark.end))
    return found


def find_clause(text, clause):
    """Return the marks of one clause kind."""
    return [mark for mark in find_clauses(text) if mark.clause is clause]
