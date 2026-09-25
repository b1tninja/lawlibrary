"""Oklahoma distribution — source and title PDF list only, no network."""

from us.states.oklahoma import Oklahoma, TITLE_PDFS


def test_source():
    assert Oklahoma.source == 'https://www.oklegislature.gov/osStatuesTitle.html'


def test_list_editions_no_network():
    editions = Oklahoma().list_editions()
    assert editions == list(TITLE_PDFS)
    assert 'https://www.oklegislature.gov/OK_Statutes/CompleteTitles/os21.pdf' in editions
    assert all(url.endswith('.pdf') for url in editions)


def test_editions_empty():
    assert Oklahoma.editions == ()
