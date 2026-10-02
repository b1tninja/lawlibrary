import datetime

from adoption import Adoption, Event, Standard, designation, edition_year, governing
from corpus import title24_corpus_path
from publication import Instrument
from us.ca import title19
from us.ca import title24
from us.ca.title24 import EDITIONS, Part, edition, section
from us.ca.title24.fire import CaliforniaFireCode, provisions, referenced

# A page of scan in the shape Public.Resource.Org's OCR gives: page furniture,
# a matrix table, numbered provisions, and a Chapter 80. The words are placeholders.
SCAN = '''2025 CALIFORNIA FIRE CODE
102102163

CALIFORNIA FIRE CODE - MATRIX ADOPTION TABLE
CHAPTER 9 - WIDGET SYSTEMS
901.6 X
903.3.1.1 X

| CHAPTER

SECTION 901—GENERAL

901.1 Scope. A widget is a widget of any occupancy.

| 901.2 Widget rooms. A widget room holds a widget and is occu-
pancy of the widget.

102102163
| N TE R N AT | 0 N AL C 0 D E C 0 T N CI ° Copyright © ICC. Accessed by someone (x@media.org) Order Number #1
9-20
WIDGET SYSTEMS

The widget room is kept
clean at all times.

901.2 or 903.3.1.1, and not a heading.

SECTION 903
AUTOMATIC WIDGETS

903.3.1.1 NFPA 13 widget systems. Widgets are installed in accordance with NFPA 13 as amended in Chapter 80.

903.3.1.1.1 Exempt locations. A room with no widget.

CHAPTER 80 - REFERENCED STANDARDS

N F PA National Fire Protection Association, 1 Batterymarch Park, Quincy, MA 02169-7471
| | 13—25: Standard for Widgets as amended*
903.3.1.1, 903.3.1.1.1,
Table 901.6.1
*NFPA 13, Amended Sections as follows:
Revise Section 2.2 as follows:
2.2 A widget standard is a widget standard.

25—13CA: California Widget Edition (Based on the 2011 Edition)
Chapter 31F, 3108F

72—99: Widget Alarm Code
907.1

U L Underwriters Laboratories LLC, 333 Pfingsten Road, Northbrook, IL 60062
38—08: Manual Widgets
907.4

APPENDIX CHAPTER 4
'''


def _lines():
    return SCAN.split('\n')


def test_an_edition_reads_its_edition_year():
    assert edition_year('25') == '2025'
    assert edition_year('04') == '2004'
    assert edition_year('96') == '1996'
    assert edition_year('2018') == '2018'
    assert edition_year('13CA') == '2013 CA'
    assert edition_year('13 CA') == '2013 CA'
    assert designation('nfpa13r') == 'NFPA 13R'
    assert designation('NFPA  25') == 'NFPA 25'


def test_a_standard_is_an_instrument_and_part_nine_is_the_fire_code():
    assert Instrument.STANDARD.value == 'standard'
    assert Part('9') is Part.FIRE
    assert Part.RESIDENTIAL.value == '2.5'
    newest = edition(Part.FIRE)
    assert newest.year == '2025' and newest.through is None
    assert edition(Part.FIRE, on=datetime.date(2025, 12, 31)).year == '2022'
    assert edition(Part.FIRE, on=datetime.date(2026, 1, 1)).year == '2025'
    assert edition(Part.FIRE, on=datetime.date(2019, 1, 1)) is None
    for chosen in EDITIONS:
        assert chosen.text_url.startswith('https://archive.org/download/%s/' % chosen.identifier)


def test_the_scan_yields_numbered_provisions_without_page_furniture():
    found = {p.number: p for p in provisions(_lines())}
    assert list(found) == ['901.1', '901.2', '903.3.1.1', '903.3.1.1.1']
    rooms = found['901.2']
    assert rooms.title == 'Widget rooms'
    assert rooms.chapter == '9' and rooms.chapter_heading == 'WIDGET SYSTEMS'
    assert rooms.parent == '901' and rooms.parent_heading == 'GENERAL'
    # A hyphen the code does not use is dropped; the page break and running head are gone.
    assert 'occupancy of the widget.' in rooms.words
    assert 'kept clean at all times.' in rooms.words
    for furniture in ('102102163', 'Copyright', 'media.org', '9-20', 'WIDGET SYSTEMS'):
        assert furniture not in rooms.words
    # A number at the start of a wrapped line is not a heading.
    assert '901.2 or 903.3.1.1, and not a heading.' in rooms.words
    # A section whose title is on the line after it.
    assert found['903.3.1.1'].parent_heading == 'AUTOMATIC WIDGETS'
    assert found['903.3.1.1'].title == 'NFPA 13 widget systems'


def test_chapter_80_names_each_standard_its_edition_and_the_amendments():
    refs = {r.standard.citation: r for r in referenced(_lines())}
    assert list(refs) == ['NFPA 13-2025', 'NFPA 25-2013 CA', 'NFPA 72-1999', 'UL 38-2008']
    thirteen = refs['NFPA 13-2025']
    assert thirteen.amended and thirteen.standard.title == 'Standard for Widgets'
    assert thirteen.via == ('903.3.1.1', '903.3.1.1.1', 'Table 901.6.1')
    assert thirteen.amendments.startswith('Revise Section 2.2')
    assert not refs['NFPA 72-1999'].amended and refs['NFPA 72-1999'].amendments == ''
    assert refs['NFPA 25-2013 CA'].via == ('Chapter 31F', '3108F')


def test_a_loaded_edition_answers_a_section_and_misses_what_it_lacks(tmp_path):
    scan = tmp_path / 'gov.ca.bsc.fire.2025_djvu.txt'
    scan.write_text(SCAN, encoding='utf-8')
    assert CaliforniaFireCode.accepts(str(scan))
    assert CaliforniaFireCode().load(str(scan), root=str(tmp_path)) == 5
    assert (tmp_path / 'US-CA' / 'title24' / '2025' / '9.sqlite').is_file()
    assert title24_corpus_path('9', '2025', root=str(tmp_path)).endswith('9.sqlite')

    hit = section('9', '903.3.1.1', root=str(tmp_path))
    assert hit['found'] and hit['citation'] == 'CFC 903.3.1.1' and hit['ocr']
    assert hit['edition']['edition'] == '2025' and 'archive.org' in hit['edition']['source']
    amendments = section(Part.FIRE, 'NFPA 13', root=str(tmp_path))
    assert amendments['found'] and amendments['chapter'] == '80'

    assert section('9', '999.9', root=str(tmp_path))['reason'] == 'not_in_index'
    assert section('9', '903.3.1.1', year='2022', root=str(tmp_path))['reason'] == 'not_indexed'
    assert section('2', '903.3.1.1', root=str(tmp_path))['reason'] == 'no_edition'
    assert section('99', '1', root=str(tmp_path))['reason'] == 'unknown_book'


def test_the_governing_edition_is_the_one_in_force_on_the_day(tmp_path):
    scan = tmp_path / 'gov.ca.bsc.fire.2025_djvu.txt'
    scan.write_text(SCAN, encoding='utf-8')
    CaliforniaFireCode().load(str(scan), root=str(tmp_path))

    permit = title24.governing('NFPA 13', on='2026-02-01', root=str(tmp_path))
    assert permit['found'] and permit['editions'] == ['2025'] and permit['rule'] == 'HSC 18938.5'
    (record,) = permit['adoptions']
    assert record['adopter'] == 'CFC 2025' and record['amended']
    assert record['amendments'] == {'part': '9', 'edition': '2025', 'section': 'NFPA 13'}
    assert permit['text'] == {'found': False, 'reason': 'standard_absent'}

    # Title 19 and the Fire Code each name NFPA 25; both readings stay.
    upkeep = title24.governing('NFPA 25', on='2026-02-01', event='inspection', root=str(tmp_path))
    assert upkeep['editions'] == ['2011', '2013 CA']
    assert {a['adopter'] for a in upkeep['adoptions']} == {'CFC 2025', title19.CITATION}

    assert title24.governing('NFPA 9999', on='2026-02-01', root=str(tmp_path))['reason'] == 'not_adopted'
    assert title24.governing('NFPA 13', on='2024-02-01', root=str(tmp_path))['reason'] == 'not_indexed'
    assert title24.governing('NFPA 13', on='2019-02-01', root=str(tmp_path))['reason'] == 'no_edition'


def test_an_adoption_covers_its_range():
    ten = Adoption('X 1', Standard('NFPA', '10', '2020'), False,
                   datetime.date(2020, 1, 1), datetime.date(2022, 12, 31))
    twelve = Adoption('Y 2', Standard('NFPA', '10', '2022'), True, datetime.date(2022, 6, 1))
    assert ten.covers(datetime.date(2022, 12, 31)) and not ten.covers(datetime.date(2023, 1, 1))
    both = governing((ten, twelve), 'NFPA 10', on='2022-07-01', event=Event.INSPECTION)
    assert both['editions'] == ['2020', '2022'] and both['rule'] == ''
    assert title19.NFPA_25.authority == ('HSC 13195',)
