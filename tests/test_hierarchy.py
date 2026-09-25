"""Agency seats read from the enactment sentence of a stored section."""

from apa import Code
from hierarchy import Seat, absent, crumbs, lineage, seats, trail
from places import Citation


def _text(book, number):
    code = book if isinstance(book, Code) else Code.get(book)
    return Citation(code).section(number).text


def test_a_department_sits_in_the_agency_the_statute_names():
    """BPC 10050. Real Estate sits in the Business and Transportation Agency."""
    found = seats(_text('BPC', '10050'), 'BPC 10050')
    if not found:
        return
    assert found[0].child == 'Department of Real Estate'
    assert found[0].parent == 'Business and Transportation Agency'
    assert found[0].frame == 'sits'


def test_a_continued_department_names_its_parent_after_itself():
    """HSC 50400. Housing sits in Business, Transportation, and Housing."""
    found = seats(_text('HSC', '50400'), 'HSC 50400')
    if not found:
        return
    assert found[0].child == 'Department of Housing and Community Development'
    assert 'Housing Agency' in found[0].parent


def test_the_roster_lists_the_agencies_under_state_government():
    """GOV 12800. The agencies sit in state government."""
    found = seats(_text('GOV', '12800'), 'GOV 12800')
    if not found:
        return
    children = {row.child for row in found}
    assert 'Natural Resources Agency' in children
    assert all(row.parent == 'state government' for row in found)


def test_a_second_in_the_is_the_parent():
    """GOV 12901. Fair Employment sits in State and Consumer Services, not in state government."""
    found = [row for row in seats(_text('GOV', '12901'), 'GOV 12901') if row.frame == 'sits']
    if not found:
        return
    assert found[0].child == 'Department of Fair Employment and Housing'
    assert found[0].parent == 'State and Consumer Services Agency'


def test_an_independent_department_records_the_agency_it_left():
    """INS 12906. Insurance left Business, Transportation and Housing."""
    found = seats(_text('INS', '12906'), 'INS 12906')
    if not found:
        return
    assert found[0].child == 'Department of Insurance'
    assert found[0].frame == 'leaves'
    assert 'Housing Agency' in found[0].parent


def test_establish_an_office_stops_before_which():
    """GOV 11340.1. The office is created. The duty that follows is not part of the name."""
    found = seats(_text('GOV', '11340.1'), 'GOV 11340.1')
    if not found:
        return
    assert found[0].child == 'Office of Administrative Law'
    assert found[0].frame == 'created'
    assert found[0].parent == ''


def test_the_crumb_is_the_outline_above_the_section():
    """BPC 10050 sits in Division 4, Part 1, Chapter 2, Article 1."""
    found = crumbs('BPC 10050')
    if not found:
        return
    assert [crumb.level for crumb in found][0] == 'code'
    assert [crumb.level for crumb in found][-1] == 'section'
    assert any('REAL ESTATE' in crumb.heading for crumb in found)
    assert 'DIVISION 4' in trail('BPC 10050')


def test_lineage_walks_the_parent_and_keeps_each_section_path():
    """Real Estate sits in an agency, and that agency sits in state government."""
    rows = [
        Seat('Department of Real Estate', 'Business and Transportation Agency', 'BPC 10050', 'sits'),
        Seat('Business and Transportation Agency', 'state government', 'GOV 12800', 'sits'),
    ]
    found = lineage('Department of Real Estate', rows)
    assert [step.office for step in found] == [
        'Business and Transportation Agency',
        'state government',
    ]
    assert found[0].crumbs
    assert found[0].crumbs[-1].heading == 'BPC 10050'


def test_a_name_the_clauses_never_place_stays_absent():
    """A catalog name with no seat is the gap."""
    rows = seats('There is in the Resources Agency the California Coastal Commission.')
    missing = absent(rows, ['California Coastal Commission', 'Department of Insurance'])
    assert missing == ['Department of Insurance']
