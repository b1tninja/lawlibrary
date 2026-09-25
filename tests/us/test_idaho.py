"""Idaho distribution — local fixture only, no network."""

import os

from us.idaho import Idaho, IdahoStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'idaho_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>55-1801. Title. This chapter shall be known as the Subdivided Lands Disposition Act.</p>
<p>55-1802. Definitions. As used in this chapter, the following terms apply.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Idaho.source == 'https://legislature.idaho.gov/statutesrules/idstat/'


def test_list_editions_no_network():
    assert Idaho().list_editions() == [
        'https://legislature.idaho.gov/statutesrules/idstat/'
    ]


def test_accepts():
    assert IdahoStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(IdahoStatutes().sections(path))
        assert len(rows) >= 2
        assert all(r['SUBDIVISION'] == Idaho.code for r in rows)
        assert rows[0]['SECTION_NUM'] == '55-1801'
        assert 'Subdivided Lands' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '55-1802'
        assert 'Definitions' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
