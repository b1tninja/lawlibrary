from corpus import connect, manual_corpus_path
from publication import Instrument
from sample import sample
from us.manuals import GpoStyleManual, HolcGuide, Manuals, OlrcGuide


OLRC = """
<html><body>
<h1>Detailed Guide</h1>
<h2 id="second">II. Section Designation and Editing</h2>
<p>A citation in square brackets was added by the editors.</p>
<h2>A. Four common types of changes</h2>
<p>Bracketed citations follow a cross reference.</p>
</body></html>
"""

HOLC = """
<html><body>
<h1>HOLC Guide to Legislative Drafting</h1>
<h2>Table of Contents</h2>
<p>Skip this list.</p>
<h2>VII. Three important conventions</h2>
<p>The office uses means, includes, shall, and may.</p>
<h3>B. The terms "shall" and "may"</h3>
<p>Shall is the office word for a duty.</p>
</body></html>
"""

GPO = """
<html><body><pre>
[Chapter 3 - Capitalization Rules]
3.1. Proper names are capitalized.
3.2. Derivatives of proper names used with a proper meaning are capitalized.
</pre></body></html>
"""


def test_olrc_headings_become_sections(tmp_path):
    path = tmp_path / 'detailed_guide.xhtml'
    path.write_text(OLRC, encoding='utf-8')
    assert OlrcGuide.accepts(path)
    assert OlrcGuide.instrument is Instrument.MANUAL
    assert OlrcGuide().load(path, root=tmp_path) == 2
    db = connect(manual_corpus_path('OLRC', root=tmp_path))
    rows = db.execute('SELECT citation, legal_text FROM section ORDER BY citation').fetchall()
    db.close()
    assert rows[0][0] == 'OLRC II'
    assert 'square brackets' in rows[0][1]
    assert rows[1][0] == 'OLRC II.A'


def test_holc_skips_the_contents_and_nests_a_letter(tmp_path):
    path = tmp_path / 'holc-guide.html'
    path.write_text(HOLC, encoding='utf-8')
    assert Manuals().load(path, root=tmp_path) == 2
    drawn = sample('HOLC', n=2, seed=1, root=tmp_path)
    assert drawn['found'] is True
    citations = {item['citation'] for item in drawn['sections']}
    assert citations == {'HOLC VII', 'HOLC VII.B'}


def test_gpo_numbers_each_rule(tmp_path):
    path = tmp_path / 'GPO-STYLEMANUAL-2008-5.htm'
    path.write_text(GPO, encoding='utf-8')
    assert GpoStyleManual().load(path, root=tmp_path) == 2
    db = connect(manual_corpus_path('GPO', root=tmp_path))
    text = db.execute("SELECT legal_text FROM section WHERE section_num = '3.2'").fetchone()[0]
    db.close()
    assert text.startswith('Derivatives')


def test_a_pdf_manual_stays_a_pointer():
    drawn = sample('CSM', kind='manual')
    assert drawn['found'] is False
    assert drawn['reason'] == 'not_indexed'
    assert 'rule1_200' in drawn['url']


def test_an_unloaded_html_manual_is_a_miss(tmp_path):
    drawn = sample('OLRC', root=tmp_path)
    assert drawn['reason'] == 'not_in_index'
    assert drawn['url'].endswith('detailed_guide.xhtml')
