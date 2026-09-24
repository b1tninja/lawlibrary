"""Virginia distribution — local CSV fixture only, no network."""

from pathlib import Path

from states.virginia import Virginia, VirginiaCode


def _write_fixture(tmp_path: Path):
    csv_text = """section,text
1-1,This Code shall be known as the Code of Virginia.
1-2,Words used in the present tense include the future.
"""
    path = tmp_path / 'title1.csv'
    path.write_text(csv_text, encoding='utf-8')
    return path


def test_source():
    assert Virginia.source == 'https://law.lis.virginia.gov/law-library/'


def test_list_editions_no_network():
    assert Virginia().list_editions() == ['https://law.lis.virginia.gov/law-library/']


def test_accepts():
    assert VirginiaCode.accepts(set())


def test_sections_from_local_csv(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(VirginiaCode().sections(path))
    assert len(rows) == 2
    assert rows[0]['SECTION_NUM'] == '1-1'
    assert 'Code of Virginia' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1-2'
    assert 'present tense' in rows[1]['LEGAL_TEXT']
