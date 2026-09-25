"""Kansas distribution — local fixture only, no network."""

import os

from us.states.kansas import Kansas, KansasStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'kansas_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><head>
<meta content="50-6,146" name="T_KSASECTEXT_S_KSANUM">
</head><body>
<p>50-6,146. Age verification. A commercial entity that knowingly publishes material harmful to minors shall verify age.</p>
<p>50-636. Civil penalties. A supplier that violates this act is liable for a civil penalty.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Kansas.source == 'https://www.kslegislature.gov/b2025_26/laws/'


def test_list_editions_no_network():
    assert Kansas().list_editions() == [
        'https://www.kslegislature.gov/b2025_26/laws/'
    ]


def test_accepts():
    assert KansasStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(KansasStatutes().sections(path))
        assert len(rows) >= 2
        assert all(r['SUBDIVISION'] == Kansas.code for r in rows)
        assert rows[0]['SECTION_NUM'] == '50-6,146'
        assert 'Age verification' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '50-636'
        assert 'Civil penalties' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
