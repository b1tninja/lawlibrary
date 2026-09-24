"""Oregon distribution — local fixture only, no network."""

import os

from us.oregon import Oregon, OregonCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'oregon_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 1.010. Definitions. As used in this chapter, the following terms apply.</p>
<p>Section 1.020. Effect of repeal. The repeal of a statute does not revive a former law.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Oregon.source == 'https://www.oregonlegislature.gov/bills_laws/pages/ors.aspx'


def test_list_editions_no_network():
    editions = Oregon().list_editions()
    assert editions == ['https://www.oregonlegislature.gov/bills_laws/pages/ors.aspx']


def test_accepts():
    assert OregonCode.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(OregonCode().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1.010'
        assert 'Definitions' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1.020'
        assert 'repeal' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
