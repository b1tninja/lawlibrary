"""Jurisdiction edges taken from vesting clauses in the index."""

from apa import Code
from places import Citation
from vesting import diagram, grants


def test_a_successor_agency_takes_the_prior_office():
    """GOV 12802. Natural Resources Agency succeeds to the Resources Agency."""
    text = Citation(Code.GOVERNMENT).section('12802').text
    if not text:
        return
    found = grants(text)
    assert found
    edge = found[0]
    assert 'Natural Resources Agency' in edge.receiver
    assert 'Resources Agency' in edge.prior
    chart = diagram(text)
    assert 'flowchart TD' in chart
    assert '-->|vested|' in chart


def test_a_bare_board_is_not_an_office():
    """An anaphoric board is not a node. A named successor and its former office are."""
    from vesting import grants
    bare = grants('The board shall succeed to, and is vested with, the duties of the board.')
    assert bare == []
    named = grants(
        'The California Gambling Control Commission shall succeed to all of the powers '
        'of the former California Gambling Control Board.'
    )
    assert named
    assert 'California Gambling Control Commission' in named[0].receiver
    assert 'California Gambling Control Board' in named[0].prior
    split = grants(
        'The Department of General Services shall succeed to, and is vested with, '
        'all duties vested in the Division of Architecture or in the State Architect.'
    )
    priors = {item.prior for item in split}
    assert 'Division of Architecture' in priors
    assert 'State Architect' in priors
