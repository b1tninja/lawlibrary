"""Virginia distribution — local CSV fixture only; annotations excluded from export."""

from pathlib import Path

from us.virginia import TITLE_1_CSV, Virginia, VirginiaCode


def _write_fixture(tmp_path: Path):
    # Column names match LIS CoVTitle_*.csv; Body is HTML; no annotation column.
    csv_text = (
        'TitleNum,TitleName,SubTitleNum,SubTitleName,PartNum,PartName,'
        'ChapterNum,ChapterName,ArticleNum,ArticleName,SubPartNum,SubPartName,'
        'Section,Title,Body\n'
        '1,General Provisions,,,,,1,CODE OF VIRGINIA,,,,,1-1,'
        'Contents and designation of Code,'
        '"<p>This Code shall be known as the Code of Virginia.</p>"\n'
        '1,General Provisions,,,,,1,CODE OF VIRGINIA,,,,,1-2,'
        'Effective date of Code,'
        '"<p>Words used in the present tense include the future.</p>"\n'
    )
    path = tmp_path / 'CoVTitle_1.csv'
    path.write_text(csv_text, encoding='utf-8')
    return path


def test_source():
    assert Virginia.source == 'https://law.lis.virginia.gov/law-library/'


def test_list_editions_no_network():
    assert Virginia().list_editions() == [TITLE_1_CSV]


def test_accepts():
    assert VirginiaCode.accepts(set())


def test_sections_from_local_csv(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(VirginiaCode().sections(path))
    assert len(rows) == 2
    assert all(r['SUBDIVISION'] == Virginia.code for r in rows)
    assert rows[0]['SECTION_NUM'] == '1-1'
    assert 'Code of Virginia' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1-2'
    assert 'present tense' in rows[1]['LEGAL_TEXT']
