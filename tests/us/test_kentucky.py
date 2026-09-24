"""Kentucky distribution — local fixture only, no network."""

import os

from us.kentucky import Kentucky, KentuckyStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'kentucky_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>KRS 446.010 Definitions for statutes generally. As used in the Kentucky Revised Statutes.</p>
<p>KRS 446.080 Liberal construction. All statutes of this state shall be liberally construed.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Kentucky.source == 'https://apps.legislature.ky.gov/law/statutes/'


def test_list_editions_no_network():
    editions = Kentucky().list_editions()
    assert editions == ['https://apps.legislature.ky.gov/law/statutes/']


def test_accepts():
    assert KentuckyStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(KentuckyStatutes().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '446.010'
        assert 'Definitions' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '446.080'
        assert 'liberally' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
