"""Arizona distribution — local fixture only, no network."""

import os

from us.arizona import Arizona, ArizonaRevisedStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'arizona_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 1-101. Short title. This publication may be cited as the Arizona Revised Statutes.</p>
<p>Section 1-102. Effect. The Arizona Revised Statutes shall be liberally construed.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Arizona.source == 'https://www.azleg.gov/ARStitle/'


def test_list_editions_no_network():
    assert Arizona().list_editions() == ['https://www.azleg.gov/ARStitle/']


def test_accepts():
    assert ArizonaRevisedStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(ArizonaRevisedStatutes().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1-101'
        assert 'Arizona Revised Statutes' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1-102'
        assert 'liberally' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
