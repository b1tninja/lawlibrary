"""Vermont distribution — local HTML fixture only, no network."""

from pathlib import Path

from us.states.vermont import Vermont, VermontStatutes


def _write_fixture(tmp_path: Path):
    html = """<!DOCTYPE html>
<html><body>
<p>§ 1 Short title. This title shall be known as the Vermont Statutes.</p>
<p>§ 2 Definitions. As used in this title, the following terms apply.</p>
</body></html>
"""
    path = tmp_path / 'vermont.html'
    path.write_text(html, encoding='utf-8')
    return path


def test_source():
    assert Vermont.source == 'https://legislature.vermont.gov/statutes'


def test_list_editions_no_network():
    assert Vermont().list_editions() == ['https://legislature.vermont.gov/statutes']


def test_accepts():
    assert VermontStatutes.accepts(set())


def test_sections_from_local_html(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(VermontStatutes().sections(path))
    assert len(rows) == 2
    assert rows[0]['SECTION_NUM'] == '1'
    assert rows[0]['SUBDIVISION'] == 'US-VT'
    assert 'Vermont Statutes' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '2'
    assert 'Definitions' in rows[1]['LEGAL_TEXT']
