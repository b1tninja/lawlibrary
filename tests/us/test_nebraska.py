"""Nebraska distribution — local fixture only, no network."""

import os

from us.nebraska import Nebraska, NebraskaStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'nebraska_fixture.xml')


def _write_fixture():
    xml = """<?xml version="1.0" encoding="utf-8"?>
<legaldoc><law type="statute"><section>
<amendatorysection chaptername="Crimes And Punishments" statutenumber="28-102">
<bookinfo>Reissue Revised Statutes of Nebraska</bookinfo>
<statuteno>28-102</statuteno>
<catchline>Purposes; principles of construction.</catchline>
<para>The general purposes of the provisions governing the definition of offenses are:</para>
<para>(1) To forbid and prevent conduct that unjustifiably and inexcusably inflicts or threatens substantial harm.</para>
</amendatorysection>
</section></law></legaldoc>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(xml)
    return FIXTURE


def test_source():
    assert Nebraska.source == 'https://github.com/nelegislature/LegalDocs'


def test_list_editions_no_network():
    assert Nebraska().list_editions() == ['https://github.com/nelegislature/LegalDocs']


def test_accepts():
    assert NebraskaStatutes.accepts(set())


def test_sections_from_local_xml():
    path = _write_fixture()
    try:
        rows = list(Nebraska().sections(path))
        assert len(rows) == 1
        assert rows[0]['SECTION_NUM'] == '28-102'
        assert 'principles of construction' in rows[0]['LEGAL_TEXT']
        assert 'forbid and prevent conduct' in rows[0]['LEGAL_TEXT']
    finally:
        os.remove(path)
