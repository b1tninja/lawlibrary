"""Indiana distribution — local zip fixture only, no network."""

import os
import zipfile

from states.indiana import Indiana, IndianaCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'indiana_fixture.zip')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>IC 1-1-1-1. Short title. This title may be cited as the Indiana Code.</p>
<p>IC 1-1-1-2. Definitions. The following definitions apply throughout this title.</p>
</body></html>
"""
    with zipfile.ZipFile(FIXTURE, 'w') as zf:
        zf.writestr('ic.html', html)
    return FIXTURE


def test_source():
    assert Indiana.source == 'https://iga.in.gov/laws/ic/downloads'


def test_list_editions_no_network():
    assert Indiana().list_editions() == ['https://iga.in.gov/laws/ic/downloads']


def test_accepts():
    assert IndianaCode.accepts(set())


def test_sections_from_local_zip():
    path = _write_fixture()
    try:
        rows = list(IndianaCode().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1-1-1-1'
        assert 'Indiana Code' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1-1-1-2'
        assert 'Definitions' in rows[1]['LEGAL_TEXT']
        # State.sections routes through the HTML-zip edition.
        via_state = list(Indiana().sections(path))
        assert via_state[0]['SECTION_NUM'] == '1-1-1-1'
    finally:
        os.remove(path)
