"""United States Code USLM indexer — synthetic fixture only, no network, no bulk XML in git."""

import zipfile
from pathlib import Path

from publication import Instrument, State
from corpus import connect, corpus_path
from us.usc import UnitedStatesCode

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
    assert rows[0]['LAW_CODE'] == '42'
    assert rows[0]['SECTION_NUM'] == '1'
    assert 'Synthetic fixture text' in rows[0]['LEGAL_TEXT']
    assert 'Synthetic fixture heading' in rows[0]['LEGAL_TEXT']
    assert 'SUBDIVISION' not in rows[0]

    assert UnitedStatesCode().load(path, root=tmp_path) == 1
    assert UnitedStatesCode().load(path, root=tmp_path) == 1  # reload replaces, no dupes
    db = connect(corpus_path('US', root=tmp_path))
    try:
        stored = db.execute(
            'SELECT pk, law_code, section_num, legal_text, citation, session '
            'FROM section ORDER BY section_num'
        ).fetchall()
        assert len(stored) == 1
        assert stored[0][0] == '42:1'
        assert stored[0][1] == '42'
        assert stored[0][2] == '1'
        assert 'Synthetic fixture text' in stored[0][3]
        assert stored[0][4] == '42 USC 1'
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
    assert rows[0]['LAW_CODE'] == '42'
    assert rows[0]['SECTION_NUM'] == '1'
    assert 'Synthetic fixture text' in rows[0]['LEGAL_TEXT']


def test_usc_corpus_path_is_us_sqlite(tmp_path):
    path = corpus_path('US', root=tmp_path)
    assert Path(path).name == 'US.sqlite'
    assert Path(path) == tmp_path / 'US.sqlite'
    assert Path(path) != tmp_path / 'US-CA.sqlite'
