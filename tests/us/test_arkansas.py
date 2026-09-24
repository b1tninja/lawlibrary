"""Arkansas distribution — Lexis only; no government corpus."""

from us.arkansas import Arkansas


def test_source():
    assert Arkansas.source == 'https://www.arkleg.state.ar.us/ArkansasLaw'


def test_editions_empty():
    assert Arkansas.editions == ()


def test_list_editions_empty():
    assert Arkansas().list_editions() == []
