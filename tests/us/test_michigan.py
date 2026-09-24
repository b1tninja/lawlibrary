"""Michigan distribution — local XML fixture only, no network."""

import os

from us.michigan import Michigan, MichiganCompiledLaws

FIXTURE = os.path.join(os.path.dirname(__file__), 'michigan_fixture.xml')


def _write_fixture():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Chapter>
  <Section>
    <SectionNumber>1.1</SectionNumber>
    <BodyText>This act shall be known and may be cited as the Michigan Compiled Laws.</BodyText>
  </Section>
  <Section>
    <SectionNumber>1.2</SectionNumber>
    <BodyText>Words and phrases used in this act shall be construed as provided in this section.</BodyText>
  </Section>
</Chapter>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(xml)
    return FIXTURE


def test_source():
    assert Michigan.source == 'https://www.legislature.mi.gov/documents/mcl/'


def test_list_editions_no_network():
    assert Michigan().list_editions() == [
        'https://www.legislature.mi.gov/documents/mcl/'
    ]


def test_accepts():
    assert MichiganCompiledLaws.accepts(set())


def test_sections_from_local_xml():
    path = _write_fixture()
    try:
        rows = list(MichiganCompiledLaws().sections(path))
        assert len(rows) == 2
        assert rows[0]['SECTION_NUM'] == '1.1'
        assert 'Michigan Compiled Laws' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1.2'
        assert 'construed' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
