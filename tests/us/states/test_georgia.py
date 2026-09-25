"""Georgia distribution — Lexis only; no government corpus."""

from us.states.georgia import Georgia


def test_source():
    assert Georgia.source == 'https://www.legis.ga.gov/'


def test_editions_empty():
    assert Georgia.editions == ()


def test_list_editions_empty():
    assert Georgia().list_editions() == []
