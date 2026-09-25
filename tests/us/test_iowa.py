"""Iowa distribution — local XML fixture only, no network."""

from pathlib import Path

from us.iowa import Iowa, IowaCode


def _write_fixture(tmp_path: Path):
    # Mirrors LSA slim chapter XML: Section elements; Text when present.
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Document>
  <Section id="sec1.1">
    <identifier>1.1</identifier>
    <Text>The boundaries of the state are as defined in the preamble.</Text>
  </Section>
  <Section id="sec1.2">
    <identifier>1.2</identifier>
    <p>The state possesses sovereignty coextensive with those boundaries.</p>
  </Section>
</Document>
"""
    path = tmp_path / 'iowa_fixture.xml'
    path.write_text(xml, encoding='utf-8')
    return path


def test_source():
    assert Iowa.source == (
        'https://www.legis.iowa.gov/docs/publications/ICC/2026/attachments/'
    )


def test_list_editions_no_network():
    assert Iowa().list_editions() == [
        'https://www.legis.iowa.gov/docs/publications/ICC/2026/attachments/'
    ]


def test_accepts():
    assert IowaCode.accepts(set())


def test_sections_from_local_xml(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(IowaCode().sections(path))
    assert len(rows) == 2
    assert all(r['SUBDIVISION'] == Iowa.code for r in rows)
    assert rows[0]['SECTION_NUM'] == '1.1'
    assert 'boundaries' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1.2'
    assert 'sovereignty' in rows[1]['LEGAL_TEXT']
