from apa import Code
from agency import Agency, CaliforniaDepartmentOfRealEstate
from places import Citation
from analysis import analyze, breakdown, capitals, compose, split_sentences
from court import Court, SacramentoSuperiorCourt
from jurisdiction import State
from mentions import Relation
from us.states.ca import California
from us.counties.ca.sacramento.cities.sacramento import Sacramento


def _dre():
    """BPC 10050. The department and the commissioner's duty, looked up."""
    text = Citation(Code.BUSINESS_AND_PROFESSIONS).section('10050').text
    if 'Department of Real Estate' not in text:
        return ''
    return text


PLACES = """
The people of the State of California do enact as follows.
The City of Sacramento sits in the County of Sacramento.
The Superior Court of the State of California, County of Sacramento hears it.
"""


def test_of_extends_the_office_and_a_number_keeps_the_unit():
    """Division of a name is the office. Division 4, and this division, are the unit."""
    office = compose('The Division of Labor Standards Enforcement shall enforce this chapter.')
    assert office[0].reading == 'office'
    assert office[0].reason == 'of'
    assert office[0].text == 'Division of Labor Standards Enforcement'
    assert office[0].noun.__name__ == 'DivisionNoun'
    unit = compose('Part 1 of Division 4 of this code applies.')
    assert any(phrase.reading == 'unit' and phrase.text == 'Division 4' for phrase in unit)
    secretary = compose('The Secretary of the Resources Agency shall succeed.')
    assert any(phrase.text == 'Secretary of the Resources Agency' and phrase.reason == 'of' for phrase in secretary)
    board = compose('The Franchise Tax Board shall administer the tax.')
    assert any(phrase.text == 'Franchise Tax Board' and phrase.reason == 'tail' for phrase in board)
    internal = compose('A subdivision of this division applies.')
    assert any(phrase.reading == 'unit' and phrase.reason == 'this' for phrase in internal)


def test_one_capitalized_word_is_a_name_and_a_capitalized_clause_is_emphasis():
    """BUYER contrasts with the sentence. A clause set entirely in capitals does not."""
    names = capitals('The party known as BUYER shall pay.')
    assert [phrase.text for phrase in names] == ['BUYER']
    assert names[0].reading == 'name'
    emphasis = capitals('NOTICE: THIS AGREEMENT IS VOID.')
    assert len(emphasis) == 1
    assert emphasis[0].reading == 'emphasis'
    assert 'BUYER' not in [phrase.text for phrase in emphasis]


def test_abbreviations_do_not_split_the_sentence():
    parts = split_sentences('See Bus. & Prof. Code § 10050. The commissioner shall enforce the provisions.')
    assert len(parts) == 2
    assert parts[0].endswith('10050.')


def test_department_is_an_instance_of_its_registered_class():
    text = _dre()
    if not text:
        return
    reading = analyze(text)
    offices = [body for body in reading.subjects if isinstance(body, Agency)]
    assert len(offices) == 1
    assert type(offices[0]) is CaliforniaDepartmentOfRealEstate
    duties = [tie for tie in offices[0].relations if getattr(tie, 'relation', None)]
    assert any(tie.relation is Relation.RESPONSIBILITY for tie in duties)
    assert any(tie.relation is Relation.SCOPE for tie in duties)


def test_unknown_office_is_a_plain_agency():
    reading = analyze('There is in the state government a Department of Widgets.')
    office = reading.subjects[0]
    assert type(office) is Agency
    assert isinstance(office, Agency)
    assert office.observed.startswith('Department of Widgets')


def test_a_reading_pins_jurisdiction_and_delegation(tmp_path):
    from analysis import pin, pins
    path = str(tmp_path / 'pins.sqlite')
    text = _dre()
    if not text:
        return
    pin(analyze(text), 'BPC 10050', path=path)
    pin(analyze(text), 'BPC 10050', path=path)
    rows = pins(citation='BPC 10050', path=path)
    jurisdiction = next(row for row in rows if row['fact'] == 'jurisdiction')
    assert jurisdiction['model'] == 'CaliforniaDepartmentOfRealEstate'
    assert jurisdiction['jurisdiction'] == 'US-CA'
    assert any(row['fact'] == 'responsibility' for row in rows)
    assert any(row['fact'] == 'establishment' for row in rows)
    assert len(pins(citation='BPC 10050', fact='jurisdiction', path=path)) == 1


def test_a_sentence_keeps_the_rule_and_the_exception():
    parts = breakdown('A lease may restrict use, except as this chapter provides, if the tenant agrees.')
    roles = [part.role for part in parts]
    assert roles[0] == 'rule'
    assert 'exception' in roles
    assert 'condition' in roles
    limited = breakdown('Subject to this chapter, a lease may restrict use, provided that the tenant agrees.')
    assert [part.role for part in limited] == ['limit', 'rule', 'limit']


def test_places_and_the_superior_court_use_their_classes():
    reading = analyze(PLACES)
    assert any(type(body) is California for body in reading.subjects)
    assert any(type(body) is Sacramento for body in reading.subjects)
    assert any(type(body) is SacramentoSuperiorCourt for body in reading.subjects)
    assert all(not isinstance(body, State) or type(body) is not State for body in reading.subjects if getattr(body, 'kind', None) and body.kind.value == 'state')
    courts = [body for body in reading.subjects if isinstance(body, Court)]
    assert courts and type(courts[0]) is not Court
