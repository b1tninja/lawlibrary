"""New Jersey distribution — synthetic text snippet only, no live zip."""

from pathlib import Path

from us.states.new_jersey import NewJersey, NewJerseyStatutes

SNIPPET = """NEW JERSEY GENERAL AND PERMANENT STATUTES

TITLE 1         ACTS, LAWS AND STATUTES

1:1-1.  General rules of construction
    In the construction of the laws and statutes of this state, both civil and criminal, words and phrases shall be read and construed with their context.

1:1-2  Words and phrases defined.
    Unless it be otherwise expressly provided, the following words and phrases shall have the meaning herein given to them.
"""


def _write_fixture(tmp_path: Path):
    path = tmp_path / 'STATUTES.TXT'
    path.write_text(SNIPPET, encoding='utf-8')
    return path


def test_source():
    assert NewJersey.source == 'https://pub.njleg.gov/statutes/STATUTES-TEXT.zip'


def test_list_editions_no_network():
    assert NewJersey().list_editions() == [
        'https://pub.njleg.gov/statutes/STATUTES-TEXT.zip'
    ]


def test_accepts():
    assert NewJerseyStatutes.accepts(set())


def test_sections_from_synthetic_snippet(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(NewJerseyStatutes().sections(path))
    assert len(rows) == 2
    assert all(r['SUBDIVISION'] == NewJersey.code for r in rows)
    assert rows[0]['SECTION_NUM'] == '1:1-1'
    assert 'construction of the laws' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1:1-2'
    assert 'Words and phrases defined' in rows[1]['LEGAL_TEXT']
