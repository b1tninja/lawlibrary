from companions import Companion, Shape, Standing, editions, load_posted, search_manual
from parsers import Guide


INDIGO = """
<html><body>
<h1>The Indigo Book</h1>
<h2>Statutes</h2>
<p>A state statute uses the code abbreviation and a section sign.</p>
</body></html>
"""


def test_posted_and_lesser_editions_are_listed():
    posted = editions(standing=Standing.POSTED)
    lesser = editions(standing=Standing.LESSER)
    assert any(row.guide is Guide.INDIGO and row.shape is Shape.HTML for row in posted)
    assert any(row.guide is Guide.BLUEBOOK for row in lesser)
    assert any(row.guide is Guide.CALIFORNIA_STYLE_MANUAL for row in posted)
    assert any(row.guide is Guide.CALIFORNIA_STYLE_MANUAL for row in lesser)
    assert all(row.source.startswith('https://') for row in editions())


def test_a_lesser_manual_is_not_fetched():
    book = next(row for row in editions(Guide.BLUEBOOK))
    missed = book.companion().read()
    assert missed['found'] is False
    assert missed['reason'] == 'lesser'
    assert missed['source'] == 'https://www.legalbluebook.com/'


def test_a_local_html_manual_is_split_on_headings(tmp_path):
    path = tmp_path / 'indigo.html'
    path.write_text(INDIGO, encoding='utf-8')
    book = next(row for row in editions(Guide.INDIGO))
    found = Companion(book).read(path)
    assert found['found'] is True
    assert found['sections'][0]['title'] == 'Statutes'
    assert 'section sign' in found['sections'][0]['text']


def test_a_posted_html_file_loads_and_can_be_searched(tmp_path):
    folder = tmp_path / 'sources'
    folder.mkdir()
    name = 'indigo-indigobook-2-1.html'
    (folder / name).write_text(INDIGO, encoding='utf-8')
    loaded = load_posted(folder, root=tmp_path)
    assert loaded[0]['guide'] == 'indigo'
    assert loaded[0]['sections'] == 1
    found = search_manual('indigo', 'section sign', root=tmp_path)
    assert found['found'] is True
    assert found['sections'][0]['title'] == 'Statutes'


def test_a_pdf_stays_a_pointer(tmp_path):
    path = tmp_path / 'manual.pdf'
    path.write_bytes(b'%PDF-1.4')
    book = next(row for row in editions(Guide.INDIGO))
    missed = book.companion().read(path)
    assert missed['reason'] == 'pdf'
