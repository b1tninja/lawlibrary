"""Utah distribution — local XML fixture only, no network."""

from pathlib import Path

from us.utah import Utah, UtahCode


def _write_fixture(tmp_path: Path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<code>
  <section number="13-1-1">Short title. This chapter is known as the Utah Code.</section>
  <section number="13-1-2">Purpose. This title promotes fair trade practices.</section>
</code>
"""
    path = tmp_path / 'utah.xml'
    path.write_text(xml, encoding='utf-8')
    return path


def test_source():
    assert Utah.source == 'https://glen.le.utah.gov/code/'


def test_list_editions_no_network():
    assert Utah().list_editions() == ['https://glen.le.utah.gov/code/']


def test_accepts():
    assert UtahCode.accepts(set())


def test_sections_from_local_xml(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(UtahCode().sections(path))
    assert len(rows) == 2
    assert rows[0]['SECTION_NUM'] == '13-1-1'
    assert 'Utah Code' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '13-1-2'
    assert 'fair trade' in rows[1]['LEGAL_TEXT']
