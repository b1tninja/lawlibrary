"""New Hampshire distribution — local fixture only, no network."""

import os

from states.new_hampshire import NewHampshire, NewHampshireRSA

FIXTURE = os.path.join(os.path.dirname(__file__), 'new_hampshire_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<h3>Section 1:1</h3>
<p><b>1:1 Perambulation.</b> The boundary lines shall be perambulated.</p>
<h3>Section 1:2</h3>
<p><b>1:2 Markers.</b> Bounds shall be renewed whenever necessary.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert NewHampshire.source == 'https://gc.nh.gov/rsa/html/NHTOC.HTM'


def test_list_editions_no_network():
    assert NewHampshire().list_editions() == ['https://gc.nh.gov/rsa/html/NHTOC.HTM']


def test_accepts():
    assert NewHampshireRSA.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(NewHampshire().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1:1'
        assert 'perambulated' in rows[0]['LEGAL_TEXT'].lower()
        assert rows[1]['SECTION_NUM'] == '1:2'
        assert 'bounds' in rows[1]['LEGAL_TEXT'].lower()
    finally:
        os.remove(path)
