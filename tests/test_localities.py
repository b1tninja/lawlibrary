"""Sacramento's codes: who serves each, and the one whose words may be read.

The City Code and the County Code are served by commercial codifiers, which
are never sources here; they are pointers to the governments' own pages.
The County's Zoning Code is published by the County itself, so it has a
parser. The fixture is a page in that site's shape with words of its own,
not the County's.
"""

from jurisdiction import Codification, Host
from us.ca.counties.sacramento import COUNTY_CODE, ZONING_CODE, SacramentoCounty
from us.ca.counties.sacramento.cities.sacramento import CITY_CODE, Sacramento
from us.ca.counties.sacramento.zoning import CODE, SacramentoZoningCode, chapter, fetch

PAGE = '''<html><head><title>Chapter 1: General Provisions | Sacramento County Land Use Regulation Library</title></head>
<body><nav><h2 id="starlight__on-this-page">On this page</h2></nav>
<h1 id="_top" class="astro-x">Chapter 1: General Provisions</h1>
<h2 id="11-title"><a class="sl-anchor-link" href="#11-title"><span aria-hidden="true">#</span><span class="sr-only">Section titled “1.1. TITLE”</span></a>1.1. TITLE</h2>
<p>This chapter is called the first chapter.</p>
<h2 id="12-scope">1.2. SCOPE</h2>
<p>It applies to <em>every</em> parcel &amp; lot.</p>
<h3 id="121-parcels">1.2.1. Parcels</h3>
<p>A parcel is a parcel.</p>
<h3 id="122">1.2.2.</h3>
<p>A lot is a lot.</p>
<h2 id="notes">Notes</h2>
<p>Not a section.</p>
</body></html>'''


def test_the_city_and_county_codes_are_pointers_and_the_zoning_code_is_readable():
    assert Sacramento.codes == (CITY_CODE,)
    assert SacramentoCounty.codes == (COUNTY_CODE, ZONING_CODE)
    assert CITY_CODE.host is Host.AMERICAN_LEGAL and not CITY_CODE.readable
    assert COUNTY_CODE.host is Host.GENERAL_CODE and not COUNTY_CODE.readable
    assert ZONING_CODE.host is Host.OFFICIAL and ZONING_CODE.readable
    for code in (CITY_CODE, COUNTY_CODE, ZONING_CODE):
        assert isinstance(code, Codification)
        assert code.pointer.startswith('https://') and 'saccounty.gov' in code.pointer or 'cityofsacramento.gov' in code.pointer
        for barred in ('amlegal', 'ecode360', 'municode', 'qcode'):
            assert barred not in code.pointer and barred not in code.text and barred not in code.ordinances
    record = ZONING_CODE.record()
    assert record['readable'] is True and record['host'] == 'official' and record['abbreviation'] == 'SZC'
    assert Host.OFFICIAL.readable and not Host.MUNICODE.readable


def test_the_place_says_what_sacramento_publishes():
    import query
    found = query.place('Sacramento')
    assert found['county'] == 'Sacramento' and found['ordinances'] == 'absent'
    titles = [code['title'] for code in found['codes']]
    assert titles == ['Sacramento City Code', 'Sacramento County Code', 'Zoning Code of Sacramento County']
    assert [code['readable'] for code in found['codes']] == [False, False, True]
    miss = query.parse_citation('Sacramento City Code 5.24.010')
    assert miss['found'] is False and miss['reason'] == 'ordinance_absent'
    assert [code['host'] for code in miss['codes']] == ['american_legal', 'general_code', 'official']


def test_a_chapter_page_yields_its_numbered_sections():
    title, found = chapter(PAGE)
    assert title == 'Chapter 1: General Provisions'
    assert [(number, heading, level) for number, heading, level, _words in found] == [
        ('1.1', 'TITLE', 2), ('1.2', 'SCOPE', 2), ('1.2.1', 'Parcels', 3), ('1.2.2', '', 3),
    ]
    words = {number: text for number, _heading, _level, text in found}
    assert words['1.1'] == 'This chapter is called the first chapter.'
    assert words['1.2'] == 'It applies to every parcel & lot.'
    assert words['1.2.2'] == 'A lot is a lot.'
    assert 'Section titled' not in words['1.1']


def test_the_zoning_code_reads_a_directory_of_saved_pages(tmp_path):
    written = fetch(str(tmp_path), pages=('ch1', 'ch2'), opener=lambda url: PAGE.encode('utf-8'))
    assert [p.rsplit('\\', 1)[-1].rsplit('/', 1)[-1] for p in written] == ['ch1.html', 'ch2.html']
    assert SacramentoZoningCode.accepts(['ch1.html', 'ch2.html']) and not SacramentoZoningCode.accepts(['ch1.html'])
    rows = list(SacramentoZoningCode().sections(str(tmp_path)))
    assert len(rows) == 8
    first = rows[0]
    assert first['LAW_CODE'] == CODE and first['PK'] == 'SZC:1.1' and first['SECTION_NUM'] == '1.1'
    assert first['LOCALITY'] == 'Sacramento County' and first['SUBDIVISION'] == 'US-CA'
    assert first['CHAPTER'] == 'ch1' and first['CHAPTER_HEADING'] == 'Chapter 1: General Provisions'
    assert SacramentoZoningCode.instrument.value == 'ordinance'
