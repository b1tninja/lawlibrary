"""Missouri distribution — local fixture only, no network."""

import os

from us.missouri import Missouri, MissouriRevisedStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'missouri_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 1.010. Revised statutes of Missouri, how cited. This revision of the statutes of Missouri shall be known as the Revised Statutes of Missouri.</p>
<p>Section 1.020. Definitions. As used in the statutory laws of this state, unless otherwise specially provided:</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Missouri.source == 'https://revisor.mo.gov/'


def test_list_editions_no_network():
    assert Missouri().list_editions() == ['https://revisor.mo.gov/']


def test_accepts():
    assert MissouriRevisedStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(MissouriRevisedStatutes().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1.010'
        assert 'Revised Statutes of Missouri' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1.020'
        assert 'Definitions' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
