"""Utah distribution — local XML fixture only; no invented token, no live fetch."""

from pathlib import Path

from us.states.utah import TOKEN_NOTE, Utah, UtahCode


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


def test_list_editions_notes_token():
    editions = Utah().list_editions()
    assert editions == [TOKEN_NOTE]
    assert 'token' in editions[0].lower()


def test_accepts():
    assert UtahCode.accepts(set())


def test_sections_from_local_xml(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(UtahCode().sections(path))
    assert len(rows) == 2
    assert all(r['SUBDIVISION'] == Utah.code for r in rows)
    assert rows[0]['SECTION_NUM'] == '13-1-1'
    assert 'Utah Code' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '13-1-2'
    assert 'fair trade' in rows[1]['LEGAL_TEXT']
