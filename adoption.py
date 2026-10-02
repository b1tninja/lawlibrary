"""Which edition of a referenced standard a code of law adopts, and when.

A code often does not print a standard. It names one: NFPA 13, 2025
edition, as amended in Chapter 80. That naming is an adoption. The code's
own words, and its own amendments to the standard, are law the government
wrote. The standard's words belong to the body that publishes it (NFPA,
ICC, UL) and are read only where a lawful copy was opened.

An adoption is in force for a date range. Which date matters is the event:
the codes in effect on the day a building permit is applied for govern the
design (Health and Safety Code section 18938.5); a system in service is
inspected under the rules in effect on the day of the inspection.
"""

import datetime
import enum
import re
from typing import NamedTuple


class Event(enum.Enum):
    """The act whose date picks the governing edition."""

    PERMIT_APPLICATION = 'permit_application'
    INSPECTION = 'inspection'


# The statute that says which date governs, where one does.
RULE = {
    Event.PERMIT_APPLICATION: 'HSC 18938.5',
    Event.INSPECTION: '',
}


_DESIGNATION = re.compile(r'^\s*(?P<publisher>[A-Za-z]+)\s*(?P<number>[0-9]+[A-Za-z]?)\s*$')


def designation(text):
    """``NFPA 13`` from ``nfpa13``, ``NFPA  13`` or ``NFPA 13``; the text itself otherwise."""
    match = _DESIGNATION.match(str(text or ''))
    if match is None:
        return str(text or '').strip()
    return '%s %s' % (match.group('publisher').upper(), match.group('number').upper())


def edition_year(token):
    """The edition a reference names, as the publisher numbers it.

    Chapter 80 of a California code writes an edition after an em dash:
    ``25`` is 2025, ``04`` is 2004, ``96`` is 1996, ``2018`` is 2018, and
    ``13CA`` or ``13 CA`` is the California edition of 2013.
    """
    text = re.sub(r'\s+', '', str(token or '')).upper()
    california = text.endswith('CA')
    digits = text[:-2] if california else text
    digits = re.match(r'\d+', digits)
    if digits is None:
        return str(token or '').strip()
    year = digits.group(0)
    if len(year) == 2:
        year = ('19' if int(year) >= 50 else '20') + year
    return year + (' CA' if california else '')


class Standard(NamedTuple):
    """One edition of a standard: ``NFPA 13``, 2025."""

    publisher: str
    number: str
    edition: str
    title: str = ''

    @property
    def designation(self):
        return '%s %s' % (self.publisher, self.number)

    @property
    def citation(self):
        return '%s-%s' % (self.designation, self.edition)

    def record(self):
        return {
            'publisher': self.publisher,
            'number': self.number,
            'designation': self.designation,
            'edition': self.edition,
            'citation': self.citation,
            'title': self.title,
        }


class Adoption(NamedTuple):
    """A code of law naming an edition of a standard, in force for a range.

    ``adopter`` is the code and edition that names it (``CFC 2025``, ``19
    CCR 901``). ``via`` is the adopter's sections that point to it.
    ``amended`` is true when the adopter amends the standard; the
    amendments are the adopter's words. ``through`` is None while the
    adoption is still in force. ``authority`` is the statute the adopter
    acts under. ``source`` is where the adoption itself was read.
    """

    adopter: str
    standard: Standard
    amended: bool
    effective: datetime.date
    through: datetime.date = None
    via: tuple = ()
    authority: tuple = ()
    source: str = ''

    def covers(self, on):
        return self.effective <= on and (self.through is None or on <= self.through)

    def record(self):
        return {
            'adopter': self.adopter,
            'standard': self.standard.record(),
            'amended': self.amended,
            'effective': self.effective.isoformat(),
            'through': self.through.isoformat() if self.through else None,
            'via': list(self.via),
            'authority': list(self.authority),
            'source': self.source,
        }


def _date(on):
    if on in (None, ''):
        return datetime.date.today()
    if isinstance(on, datetime.datetime):
        return on.date()
    if isinstance(on, datetime.date):
        return on
    return datetime.date.fromisoformat(str(on).strip())


def governing(adoptions, standard, on=None, event=Event.PERMIT_APPLICATION):
    """The adoptions of ``standard`` in force on ``on`` for ``event``.

    Every adopter in force is returned. When two adopters name different
    editions for the same day, both stay in ``adoptions`` and ``editions``
    lists each; the lookup does not pick one. A standard no adopter names
    on that day is a miss, ``not_adopted``. The standard's own words are
    not held here: ``text`` is a miss, ``standard_absent``, unless a caller
    that opened a lawful copy fills it.
    """
    wanted = designation(standard)
    event = Event(event) if not isinstance(event, Event) else event
    day = _date(on)
    found = [a for a in adoptions if a.standard.designation == wanted and a.covers(day)]
    found.sort(key=lambda a: (a.effective, a.adopter))
    result = {
        'standard': wanted,
        'on': day.isoformat(),
        'event': event.value,
        'rule': RULE[event],
    }
    if not found:
        named = sorted({a.standard.edition for a in adoptions if a.standard.designation == wanted})
        return dict(result, found=False, reason='not_adopted', editions_named=named)
    editions = sorted({a.standard.edition for a in found})
    return dict(
        result,
        found=True,
        editions=editions,
        adoptions=[a.record() for a in found],
        text={'found': False, 'reason': 'standard_absent'},
    )
