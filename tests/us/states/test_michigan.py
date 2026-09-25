"""Michigan distribution — local XML fixture only, no network."""

from pathlib import Path

from us.states.michigan import Michigan, MichiganCompiledLaws


def _write_fixture(tmp_path: Path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Chapter>
  <Section>
    <SectionNumber>1.1</SectionNumber>
    <BodyText>This act shall be known and may be cited as the Michigan Compiled Laws.</BodyText>
  </Section>
  <Section>
    <MCLNumber>1.2</MCLNumber>
    <BodyText>Words and phrases used in this act shall be construed as provided in this section.</BodyText>
  </Section>
</Chapter>
"""
    path = tmp_path / 'michigan_fixture.xml'
    path.write_text(xml, encoding='utf-8')
    return path


def test_source():
    assert Michigan.source == 'https://www.legislature.mi.gov/documents/mcl/'


def test_list_editions_no_network():
    assert Michigan().list_editions() == [
        'https://www.legislature.mi.gov/documents/mcl/'
    ]


def test_accepts():
    assert MichiganCompiledLaws.accepts(set())


def test_sections_from_local_xml(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(MichiganCompiledLaws().sections(path))
    assert len(rows) == 2
    assert all(r['SUBDIVISION'] == Michigan.code for r in rows)
    assert rows[0]['SECTION_NUM'] == '1.1'
    assert 'Michigan Compiled Laws' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1.2'
    assert 'construed' in rows[1]['LEGAL_TEXT']
