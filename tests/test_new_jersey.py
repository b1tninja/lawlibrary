"""New Jersey distribution — local fixture only, no network."""

import os
import zipfile

from states.new_jersey import NewJersey, NewJerseyStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'new_jersey_fixture.zip')


def _write_fixture():
    text = (
        "TITLE 1. GENERAL PROVISIONS\n"
        "1:1-1. Words and phrases defined. As used in this Title...\n"
        "The statutes of New Jersey shall be known as the New Jersey Statutes.\n"
    )
    with zipfile.ZipFile(FIXTURE, 'w') as zf:
        zf.writestr('STATUTES-TEXT.txt', text)
    return FIXTURE


def test_source():
    assert NewJersey.source == 'https://pub.njleg.gov/statutes/STATUTES-TEXT.zip'


def test_list_editions_no_network():
    assert NewJersey().list_editions() == [
        'https://pub.njleg.gov/statutes/STATUTES-TEXT.zip'
    ]


def test_accepts():
    assert NewJerseyStatutes.accepts(set())


def test_sections_from_local_zip():
    path = _write_fixture()
    try:
        rows = list(NewJersey().sections(path))
        assert len(rows) == 1
        assert rows[0]['SECTION_NUM'] == 'STATUTES-TEXT'
        assert 'New Jersey Statutes' in rows[0]['LEGAL_TEXT']
        assert '1:1-1' in rows[0]['LEGAL_TEXT']
    finally:
        os.remove(path)
