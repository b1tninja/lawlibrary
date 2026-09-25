"""Minnesota distribution — local fixture only, no network."""

import os

from us.states.minnesota import Minnesota, MinnesotaStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'minnesota_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 645.08. Canons of construction. In construing the statutes of this state, the following canons of interpretation apply.</p>
<p>Section 645.16. Intent of the legislature. The object of all interpretation is to ascertain the intention of the legislature.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Minnesota.source == 'https://www.revisor.mn.gov/statutes/'


def test_list_editions_no_network():
    assert Minnesota().list_editions() == [
        'https://www.revisor.mn.gov/statutes/'
    ]


def test_accepts():
    assert MinnesotaStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(MinnesotaStatutes().sections(path))
        assert len(rows) >= 2
        assert all(r['SUBDIVISION'] == Minnesota.code for r in rows)
        assert rows[0]['SECTION_NUM'] == '645.08'
        assert 'canons' in rows[0]['LEGAL_TEXT'].lower()
        assert rows[1]['SECTION_NUM'] == '645.16'
        assert 'legislature' in rows[1]['LEGAL_TEXT'].lower()
    finally:
        os.remove(path)
