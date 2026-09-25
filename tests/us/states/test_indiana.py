"""Indiana distribution — local HTML / zip fixtures only, no network."""

import zipfile
from pathlib import Path

from us.states.indiana import Indiana, IndianaCode

HTML = """<!DOCTYPE html>
<html><body>
<p>IC 1-1-1-1. Short title. This title may be cited as the Indiana Code.</p>
<p>IC 1-1-1-2. Definitions. The following definitions apply throughout this title.</p>
</body></html>
"""


def test_source():
    assert Indiana.source == 'https://iga.in.gov/laws/ic/downloads'


def test_list_editions_no_network():
    assert Indiana().list_editions() == ['https://iga.in.gov/laws/ic/downloads']


def test_accepts():
    assert IndianaCode.accepts(set())


def test_sections_from_local_html(tmp_path):
    path = tmp_path / 'ic.html'
    path.write_text(HTML, encoding='utf-8')
    rows = list(IndianaCode().sections(path))
    assert len(rows) >= 2
    assert all(r['SUBDIVISION'] == Indiana.code for r in rows)
    assert all(r['LAW_CODE'] == 'IC' for r in rows)
    assert rows[0]['SECTION_NUM'] == '1-1-1-1'
    assert 'Indiana Code' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1-1-1-2'
    assert 'Definitions' in rows[1]['LEGAL_TEXT']


def test_sections_from_local_zip(tmp_path):
    path = tmp_path / 'indiana_fixture.zip'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('ic.html', HTML)
    rows = list(Indiana().sections(path))
    assert rows[0]['SECTION_NUM'] == '1-1-1-1'
    assert rows[0]['SUBDIVISION'] == Indiana.code
