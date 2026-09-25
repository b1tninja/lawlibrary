"""Pennsylvania distribution — list_editions and source only; no network."""

from us.states.pennsylvania import Pennsylvania


def test_source():
    assert Pennsylvania.source == 'https://www.palegis.us/statutes/consolidated'


def test_editions_empty():
    assert Pennsylvania.editions == ()


def test_list_editions_concrete_pdf_urls():
    editions = Pennsylvania().list_editions()
    assert editions == [
        'https://www.legis.state.pa.us/WU01/LI/LI/CT/PDF/18/18.PDF',
        'https://www.legis.state.pa.us/WU01/LI/LI/CT/PDF/01/01.PDF',
    ]
