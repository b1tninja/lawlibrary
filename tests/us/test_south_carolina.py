"""South Carolina distribution — local fixture only, no network."""

import os

from us.south_carolina import SouthCarolina, SouthCarolinaCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'south_carolina_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 16-1-10. Felonies and misdemeanors. Offenses are classified as provided in this chapter.</p>
<p>Section 16-1-20. Classification of offenses. The following classifications apply.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert SouthCarolina.source == 'https://www.scstatehouse.gov/code/statmast.php'


def test_list_editions_no_network():
    editions = SouthCarolina().list_editions()
    assert editions == ['https://www.scstatehouse.gov/code/statmast.php']


def test_accepts():
    assert SouthCarolinaCode.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(SouthCarolinaCode().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '16-1-10'
        assert 'Felonies' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '16-1-20'
        assert 'Classification' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
