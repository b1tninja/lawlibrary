"""United States Code USLM indexer — synthetic fixture only, no network, no bulk XML in git."""

import zipfile
from pathlib import Path

from publication import Instrument, State
from corpus import connect, corpus_path
from us.usc import AnnualCode, UnitedStatesCode, locate_archive, locate_release

# Tiny synthetic USLM ``<section>`` only. Not live Code text.
FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<uscDoc xmlns="http://xml.house.gov/schemas/uslm/1.0" identifier="/us/usc/t42">
  <main>
    <title identifier="/us/usc/t42">
      <num value="42">Title 42—</num>
      <heading>Synthetic title heading</heading>
      <section identifier="/us/usc/t42/s1" id="id-s1">
        <num value="1">§1.</num>
        <heading>Synthetic fixture heading.</heading>
        <content>
          <p>Synthetic fixture text for the USLM parser test.</p>
        </content>
      </section>
    </title>
  </main>
</uscDoc>
"""


def _write_fixture(tmp_path: Path):
    path = tmp_path / 'usc42.xml'
    path.write_text(FIXTURE, encoding='utf-8')
    return path


def test_not_a_state():
    assert not issubclass(UnitedStatesCode, State)


def test_instrument_is_statute():
    assert UnitedStatesCode.instrument is Instrument.STATUTE


def test_the_download_page_names_xml_release_points():
    from us.usc import xml_downloads
    page = (
        '<a href="releasepoints/us/pl/119/111/xml_usc42@119-111.zip">XML</a>'
        '<a href="releasepoints/us/pl/119/111/htm_usc42@119-111.zip">XHTML</a>'
        '<a href="releasepoints/us/pl/119/111/xml_uscAll@119-111.zip">XML</a>'
    )
    found = xml_downloads(page)
    assert found[0]['congress'] == '119'
    assert found[0]['law'] == '111'
    assert found[0]['url'].endswith('/xml_usc42@119-111.zip')
    assert found[1]['url'].endswith('/xml_uscAll@119-111.zip')
    assert all('htm_usc' not in item['url'] for item in found)


def test_accepts_title_xml_names():
    assert UnitedStatesCode.accepts({'usc42.xml'})
    assert UnitedStatesCode.accepts(['path/to/usc1.xml', 'readme.txt'])
    assert UnitedStatesCode.accepts('usc42.xml')
    assert UnitedStatesCode.accepts('/tmp/usc42.xml')
    assert not UnitedStatesCode.accepts({'readme.txt'})
    assert not UnitedStatesCode.accepts({'LAW_SECTION_TBL'})
    assert not UnitedStatesCode.accepts('xhtml_usc42.zip')
    assert not UnitedStatesCode.accepts('pdf_usc42.zip')


def test_sections_from_synthetic_fixture(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(UnitedStatesCode().sections(path))
    assert len(rows) == 1
    assert rows[0]['COUNTRY'] == 'US'
    assert rows[0]['SUBDIVISION'] == 'US'
    assert rows[0]['LAW_CODE'] == '42USC'
    assert rows[0]['SECTION_NUM'] == '1'
    assert 'Synthetic fixture text' in rows[0]['LEGAL_TEXT']
    assert 'Synthetic fixture heading' in rows[0]['LEGAL_TEXT']
    assert 'Title 42' in rows[0]['CODE_HEADING']
    assert rows[0]['TITLE'] == '42'
    assert rows[0]['TITLE_HEADING'] == 'Synthetic title heading'

    assert UnitedStatesCode().load(path, root=tmp_path) == 1
    assert UnitedStatesCode().load(path, root=tmp_path) == 1  # reload replaces, no dupes
    db = connect(corpus_path('US', root=tmp_path))
    try:
        stored = db.execute(
            'SELECT pk, law_code, section_num, legal_text, citation, session '
            'FROM section ORDER BY section_num'
        ).fetchall()
        assert len(stored) == 1
        assert stored[0][0] == '42USC:1'
        assert stored[0][1] == '42USC'
        assert stored[0][2] == '1'
        assert 'Synthetic fixture text' in stored[0][3]
        assert stored[0][4] == '42USC 1'
        assert stored[0][5] == ''
    finally:
        db.close()


def test_sections_from_synthetic_zip(tmp_path):
    path = tmp_path / 'xml_usc42@119-111.zip'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('usc42.xml', FIXTURE)
    rows = list(UnitedStatesCode().sections(path))
    assert len(rows) == 1
    assert rows[0]['COUNTRY'] == 'US'
    assert rows[0]['LAW_CODE'] == '42USC'
    assert rows[0]['SECTION_NUM'] == '1'
    assert 'Synthetic fixture text' in rows[0]['LEGAL_TEXT']


ARCHIVE = """<html><body>
<!-- itempath:/420/CHAPTER 126/Sec. 12101 -->
<p class="statutory-body">Synthetic archive section.</p>
<!-- itempath:/420/CHAPTER 126/Sec. 12102 -->
<p class="statutory-body">Next archive section.</p>
</body></html>
"""


def test_a_code_section_opens_the_current_classification():
    from us.usc import locate_section
    href = locate_section(42, 12101)
    assert href.startswith('https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title42-section12101')


def test_an_archive_year_is_xhtml_and_a_release_point_is_xml():
    assert locate_archive(1994, 42).endswith('/XHTML/1994/1994usc42.htm')
    assert locate_archive(1994, '5a').endswith('/1994usc05a.htm')
    assert locate_archive(1994).endswith('/XHTML/1994.zip')
    assert locate_release(113, 21, 42).endswith('/pl/113/21/xml_usc42@113-21.zip')
    assert locate_release(119, 111).endswith('/xml_uscAll@119-111.zip')
    assert AnnualCode.accepts('1994usc42.htm')
    assert not AnnualCode.accepts('usc42.zip')
    assert not AnnualCode.accepts('1994usc42.pdf')


def test_archive_sections_follow_the_itempath(tmp_path):
    path = tmp_path / '1994usc42.htm'
    path.write_text(ARCHIVE, encoding='utf-8')
    rows = list(AnnualCode().sections(path))
    assert rows[0]['SECTION_NUM'] == '12101'
    assert rows[0]['LAW_CODE'] == '42USC'
    assert rows[0]['SESSION'] == '1994'
    assert rows[0]['CITATION'] == '42USC 12101'
    assert 'Synthetic archive section' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '12102'


def test_fetch_writes_the_archive_and_the_release_point(tmp_path):
    def opener(url):
        return b'official-file'

    saved = AnnualCode().fetch(1994, tmp_path, title=42, opener=opener)
    assert saved.endswith('1994usc42.htm')
    release = UnitedStatesCode().fetch(113, 21, tmp_path, title=42, opener=opener)
    assert release.endswith('xml_usc42@113-21.zip')
    whole = AnnualCode().fetch(1994, tmp_path, opener=opener)
    assert whole.endswith('1994.zip')


def test_usc_corpus_path_is_us_sqlite(tmp_path):
    path = corpus_path('US', root=tmp_path)
    assert Path(path).name == 'US.sqlite'
    assert Path(path) == tmp_path / 'US.sqlite'
    assert Path(path) != tmp_path / 'US-CA.sqlite'
