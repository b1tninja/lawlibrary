"""Marks that build an outline: a roman numeral, and the indent of a line.

A roman numeral is the printed token and its value. ``IIII`` is not a
numeral. A miss is ``None``. A single ``i``, ``v``, or ``x`` is a numeral
and also a letter, so a subdivision rank still treats it as a letter.

A margin is the leading spaces and tabs. The California code index does
not keep that indent. When a later line sits further in, it is a child of
the line above it.
"""

import re


_VALUES = (
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
    (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
    (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I'),
)
_AMOUNT = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


class Roman:
    """One roman numeral. ``text`` is the printed token. ``value`` is the integer."""

    def __init__(self, text, value):
        self.text = text
        self.value = value

    @classmethod
    def read(cls, text):
        """The numeral, or ``None`` when the token is not a canonical roman."""
        token = (text or '').strip()
        if not token or re.fullmatch(r'[IVXLCDMivxlcdm]+', token) is None:
            return None
        value = _amount(token.upper())
        if value is None or format_roman(value) != token.upper():
            return None
        return cls(token, value)


def format_roman(value):
    """The uppercase numeral for a positive integer."""
    number = int(value)
    if number < 1:
        raise ValueError(value)
    parts = []
    for amount, glyph in _VALUES:
        while number >= amount:
            parts.append(glyph)
            number -= amount
    return ''.join(parts)


def _amount(token):
    total = 0
    previous = 0
    for glyph in reversed(token):
        amount = _AMOUNT[glyph]
        if amount < previous:
            total -= amount
        else:
            total += amount
            previous = amount
    return total


class Margin:
    """Leading whitespace on one line. A tab is wider than a space."""

    def __init__(self, spaces, tabs):
        self.spaces = spaces
        self.tabs = tabs

    @classmethod
    def read(cls, line):
        spaces = 0
        tabs = 0
        for glyph in line or '':
            if glyph == ' ':
                spaces += 1
            elif glyph == '\t':
                tabs += 1
            else:
                break
        return cls(spaces, tabs)

    def __eq__(self, other):
        return (self.tabs, self.spaces) == (other.tabs, other.spaces)

    def __gt__(self, other):
        return (self.tabs, self.spaces) > (other.tabs, other.spaces)

    def __ge__(self, other):
        return self > other or self == other
