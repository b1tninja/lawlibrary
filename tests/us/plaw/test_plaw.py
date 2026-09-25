"""Public law locator and USLM parser. No network."""

from publication import Instrument
from us.plaw import PublicLaws, locate

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<pLaw xmlns="http://schemas.gpo.gov/xml/uslm">
  <meta>
    <congress>117</congress>
    <docNumber>58</docNumber>
  </meta>
  <main><p>Synthetic public law text.</p></main>
</pLaw>
"""


def test_a_recent_law_is_gpo_xml_and_an_older_law_is_the_slip():
    assert locate(117, 58).endswith('/PLAW/117/public/PLAW-117publ58.xml')
    assert locate(101, 336).endswith('/101/plaws/publ336/PLAW-101publ336.pdf')
    assert PublicLaws.instrument is Instrument.STATUTE
    assert PublicLaws.accepts('PLAW-117publ58.xml')
    assert not PublicLaws.accepts('PLAW-101publ336.pdf')


def test_sections_read_the_congress_and_the_law_number(tmp_path):
    path = tmp_path / 'PLAW-117publ58.xml'
    path.write_text(FIXTURE, encoding='utf-8')
    rows = list(PublicLaws().sections(path))
    assert rows[0]['CITATION'] == 'PL 117 58'
    assert rows[0]['SECTION_NUM'] == '117-58'
    assert rows[0]['COUNTRY'] == 'US'
    assert 'Synthetic public law text' in rows[0]['LEGAL_TEXT']


def test_fetch_writes_the_official_file(tmp_path):
    def opener(url):
        assert url.endswith('PLAW-117publ58.xml')
        return FIXTURE.encode('utf-8')

    saved = PublicLaws().fetch(117, 58, tmp_path, opener=opener)
    assert saved.endswith('PLAW-117publ58.xml')
    assert list(PublicLaws().sections(saved))[0]['CITATION'] == 'PL 117 58'
