"""Alaska distribution — list_editions and source only; no network."""

from us.states.alaska import Alaska


def test_source():
    assert Alaska.source == 'https://www.akleg.gov/statutesPDF/Title-1.pdf'


def test_editions_empty():
    assert Alaska.editions == ()


def test_list_editions_concrete_pdf_urls():
    editions = Alaska().list_editions()
    assert editions == [
        'https://www.akleg.gov/statutesPDF/Title-1.pdf',
        'https://www.akleg.gov/statutesPDF/Title-2.pdf',
        'https://www.akleg.gov/statutesPDF/Title-3.pdf',
        'https://www.akleg.gov/statutesPDF/Title-4.pdf',
        'https://www.akleg.gov/statutesPDF/Title-5.pdf',
    ]
