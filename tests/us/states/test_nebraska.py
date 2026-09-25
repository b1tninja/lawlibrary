"""Nebraska distribution — local fixture only, no network."""

from pathlib import Path

from us.states.nebraska import Nebraska, NebraskaStatutes


def _write_fixture(tmp_path: Path):
    xml = """<?xml version="1.0" encoding="utf-8"?>
<legaldoc><law type="statute"><section>
<amendatorysection chaptername="Crimes And Punishments" statutenumber="28-102">
<bookinfo>Reissue Revised Statutes of Nebraska</bookinfo>
<statuteno>28-102</statuteno>
<catchline>Purposes; principles of construction.</catchline>
<para>The general purposes of the provisions governing the definition of offenses are:</para>
<para>(1) To forbid and prevent conduct that unjustifiably and inexcusably inflicts or threatens substantial harm.</para>
</amendatorysection>
</section>
<source>Laws 1977.</source>
<annotation><para>Case note that must not appear in LEGAL_TEXT. State v. Example, 1 Neb. 1 (1900).</para></annotation>
</law></legaldoc>
"""
    path = tmp_path / 'nebraska_fixture.xml'
    path.write_text(xml, encoding='utf-8')
    return path


def test_source():
    assert Nebraska.source == 'https://github.com/nelegislature/LegalDocs'


def test_list_editions_no_network():
    assert Nebraska().list_editions() == ['https://github.com/nelegislature/LegalDocs']


def test_accepts():
    assert NebraskaStatutes.accepts(set())


def test_sections_from_local_xml(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(Nebraska().sections(path))
    assert len(rows) == 1
    assert rows[0]['SUBDIVISION'] == Nebraska.code
    assert rows[0]['SECTION_NUM'] == '28-102'
    assert 'principles of construction' in rows[0]['LEGAL_TEXT']
    assert 'forbid and prevent conduct' in rows[0]['LEGAL_TEXT']
    assert 'Case note' not in rows[0]['LEGAL_TEXT']
    assert 'State v. Example' not in rows[0]['LEGAL_TEXT']
