"""Title 24 of the California Code of Regulations, the Building Standards Code.

The California Building Standards Commission publishes Title 24 every three
years (Health and Safety Code sections 18901, 18902, 18930 et seq.). Most
parts are a model code with California's amendments printed in place, sold
by the model code's publisher; the state keeps no text edition of its own.
Public.Resource.Org scanned each edition as law and posted it to the
Internet Archive with its OCR text (``_djvu.txt``). That text is read here.
It is OCR: a word can be wrong, and a table is flattened to lines.

An edition is in force from its effective date. The edition in force on
the day a building permit is applied for governs that building (Health and
Safety Code section 18938.5), so an older edition stays readable after the
next one takes effect. See ``docs/special/title-24.md`` and
``docs/special/nfpa.md``.
"""

import datetime
import enum
import os
import sqlite3
import urllib.request
from typing import NamedTuple

from corpus import title24_corpus_path

ARCHIVE = 'https://archive.org'


class Part(enum.Enum):
    """The parts of Title 24. The value is the part number."""

    ADMINISTRATIVE = '1'
    BUILDING = '2'
    RESIDENTIAL = '2.5'
    ELECTRICAL = '3'
    MECHANICAL = '4'
    PLUMBING = '5'
    ENERGY = '6'
    WILDLAND_URBAN_INTERFACE = '7'
    HISTORICAL_BUILDING = '8'
    FIRE = '9'
    EXISTING_BUILDING = '10'
    GREEN_BUILDING = '11'
    REFERENCED_STANDARDS = '12'


# The name a citation uses for a part: ``CFC 903.3.1.1``.
ABBREVIATION = {
    Part.BUILDING: 'CBC',
    Part.RESIDENTIAL: 'CRC',
    Part.FIRE: 'CFC',
}


class Edition(NamedTuple):
    """One triennial edition of one part, and the scan its words come from.

    ``through`` is the last day a permit application falls under this
    edition; None while it is the newest.
    """

    part: Part
    year: str
    published: datetime.date
    effective: datetime.date
    through: datetime.date
    identifier: str

    @property
    def abbreviation(self):
        return ABBREVIATION.get(self.part, 'T24-%s' % self.part.value)

    @property
    def name(self):
        return '%s %s' % (self.abbreviation, self.year)

    @property
    def page(self):
        return '%s/details/%s' % (ARCHIVE, self.identifier)

    @property
    def text_url(self):
        return '%s/download/%s/%s_djvu.txt' % (ARCHIVE, self.identifier, self.identifier)

    @property
    def filename(self):
        return '%s_djvu.txt' % self.identifier

    def covers(self, on):
        return self.effective <= on and (self.through is None or on <= self.through)

    def record(self):
        return {
            'part': self.part.value,
            'code': self.abbreviation,
            'edition': self.year,
            'published': self.published.isoformat(),
            'effective': self.effective.isoformat(),
            'through': self.through.isoformat() if self.through else None,
            'source': self.page,
        }


# Information Bulletin 25-01: the 2025 edition was published 2025-07-01 and
# took effect 2026-01-01; the 2022 edition governs permits applied for
# through 2025-12-31.
EDITIONS = (
    Edition(Part.FIRE, '2022', datetime.date(2022, 7, 1), datetime.date(2023, 1, 1),
            datetime.date(2025, 12, 31), '2022californiafi00unse'),
    Edition(Part.FIRE, '2025', datetime.date(2025, 7, 1), datetime.date(2026, 1, 1),
            None, 'gov.ca.bsc.fire.2025'),
)


def edition(part, year=None, on=None):
    """The edition of ``part`` named by ``year``, or in force on ``on``, or the newest."""
    part = part if isinstance(part, Part) else Part(str(part))
    mine = [e for e in EDITIONS if e.part is part]
    if year:
        mine = [e for e in mine if e.year == str(year)]
    elif on is not None:
        mine = [e for e in mine if e.covers(on)]
    return mine[-1] if mine else None


def source_dir(root=None):
    """Where the scans' text is saved: ``data/title24``. Not committed."""
    if root is not None:
        return root
    from core import data_dir
    return os.path.join(str(data_dir()), 'title24')


def fetch(chosen, dest=None):
    """Save one edition's OCR text from the Internet Archive; return its path."""
    folder = source_dir(dest)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, chosen.filename)
    if not os.path.isfile(path):
        request = urllib.request.Request(chosen.text_url, headers={'User-Agent': 'lawlibrary'})
        with urllib.request.urlopen(request) as response, open(path + '.part', 'wb') as out:
            out.write(response.read())
        os.replace(path + '.part', path)
    return path


def adoptions(root=None):
    """Every adoption of a standard California's loaded codes record.

    The Fire Code editions come from their Chapter 80, once loaded; Title 19
    is recorded by hand (``us.ca.title19``).
    """
    from us.ca.title19 import ADOPTIONS
    from us.ca.title24.fire import adoptions as fire_code
    return list(fire_code(root=root)) + list(ADOPTIONS)


def governing(standard, on=None, event='permit_application', root=None):
    """Which edition of ``standard`` California's codes name on ``on`` for ``event``.

    A Fire Code adoption the code amends points to the row that holds
    California's amendments (``section(Part.FIRE, 'NFPA 13', year)``).
    """
    from adoption import governing as pick
    try:
        result = pick(adoptions(root=root), standard, on=on, event=event)
    except ValueError as error:
        return {'found': False, 'standard': str(standard), 'reason': 'bad_request', 'detail': str(error)}
    day = datetime.date.fromisoformat(result['on'])
    if not result['found']:
        # The Fire Code's silence is a finding only when its edition for that day was read.
        chosen = edition(Part.FIRE, on=day)
        if chosen is None:
            result['reason'] = 'no_edition'
        elif not os.path.isfile(title24_corpus_path(Part.FIRE.value, chosen.year, root=root)):
            result['reason'] = 'not_indexed'
    for record in result.get('adoptions', ()):
        code, _, year = record['adopter'].partition(' ')
        if record['amended'] and code == ABBREVIATION[Part.FIRE]:
            record['amendments'] = {
                'part': Part.FIRE.value, 'edition': year, 'section': record['standard']['designation'],
            }
    return result


def _miss(citation, reason, **extra):
    return dict({'found': False, 'citation': citation, 'reason': reason}, **extra)


def _day(on):
    if on in (None, ''):
        return None
    if isinstance(on, datetime.date):
        return on
    return datetime.date.fromisoformat(str(on).strip())


def section(part, number, year=None, on=None, root=None):
    """One section of a loaded Title 24 edition, or a miss.

    ``year`` names the edition; ``on`` picks the edition in force that day
    (the permit application date); neither picks the newest. A part with no
    known edition is ``no_edition``; an edition whose file is not loaded is
    ``not_indexed``; a number the edition does not have is ``not_in_index``.
    """
    try:
        part = part if isinstance(part, Part) else Part(str(part))
    except ValueError:
        return _miss('Title 24 Part %s %s' % (part, number), 'unknown_book')
    try:
        day = _day(on)
    except ValueError as error:
        return _miss('Title 24 Part %s %s' % (part.value, number), 'bad_request', detail=str(error))
    chosen = edition(part, year=year, on=day)
    label = '%s %s' % (ABBREVIATION.get(part, 'T24-%s' % part.value), number)
    if chosen is None:
        return _miss(label, 'no_edition', edition=str(year or ''), on=day.isoformat() if day else '')
    path = title24_corpus_path(part.value, chosen.year, root=root)
    if not os.path.isfile(path):
        return _miss(label, 'not_indexed', edition=chosen.record())
    db = sqlite3.connect(path)
    try:
        row = db.execute(
            'SELECT s.pk, s.legal_text, s.citation, p.title, p.chapter, p.chapter_heading, '
            'p.parent, p.parent_heading FROM section s LEFT JOIN provision p ON p.pk = s.pk '
            'WHERE s.section_num = ?',
            (str(number).strip(),),
        ).fetchone()
    except sqlite3.Error:
        row = None
    finally:
        db.close()
    if row is None:
        return _miss(label, 'not_in_index', edition=chosen.record())
    pk, text, citation, title, chapter, chapter_heading, parent, parent_heading = row
    return {
        'found': True,
        'citation': citation,
        'code': chosen.abbreviation,
        'section': str(number).strip(),
        'title': title or '',
        'text': text or '',
        'chapter': chapter or '',
        'chapter_heading': chapter_heading or '',
        'parent': parent or '',
        'parent_heading': parent_heading or '',
        'edition': chosen.record(),
        'ocr': True,
    }
