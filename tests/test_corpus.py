from jurisdiction import Country, Region
from us import UnitedStates
from us.states.ca import California
from us.counties.ca.sacramento import SacramentoCounty
from us.counties.ca.sacramento.cities.sacramento import Sacramento

from corpus import Catalog, alias_for, connect, corpus_path, corpus_path_for, statute_corpus_path


def test_entities_include_california_and_departments():
    from entities import list_entities
    kinds = {row['kind'] for row in list_entities()}
    assert {'country', 'state', 'county', 'city', 'department'} <= kinds
    states = [row for row in list_entities('state') if row['code'] == 'US-CA']
    assert states and states[0]['name']
    departments = list_entities('department')
    assert any(row['name'] == 'Office of Administrative Law' and row['parent'] == 'US-CA' for row in departments)


def test_federal_and_state_are_separate_files(tmp_path):
    federal = corpus_path('US', root=tmp_path)
    state = corpus_path('US', 'US-CA', root=tmp_path)
    assert federal.endswith('US.sqlite')
    assert state.endswith('US-CA.sqlite')
    assert federal != state


def test_older_session_is_its_own_file(tmp_path):
    current = corpus_path('US', 'US-CA', root=tmp_path)
    older = corpus_path('US', 'US-CA', session='2009', root=tmp_path)
    assert current != older
    assert older.endswith('2009.sqlite')


def test_city_sits_under_its_county(tmp_path):
    county = corpus_path_for(SacramentoCounty, root=tmp_path)
    city = corpus_path_for(Sacramento, root=tmp_path)
    assert county.endswith('US-CA/sacramento.sqlite') or county.endswith('US-CA\\sacramento.sqlite')
    assert 'sacramento' in city and city.endswith('sacramento.sqlite')
    assert county != city
    assert corpus_path_for(California, root=tmp_path).endswith('US-CA.sqlite')
    assert corpus_path_for(UnitedStates, root=tmp_path).endswith('US.sqlite')


def test_connect_creates_the_section_table(tmp_path):
    path = corpus_path('US', 'US-CA', root=tmp_path)
    db = connect(path)
    rows = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='section'").fetchall()
    assert rows == [('section',)]
    db.close()


def test_attach_keeps_each_subdivision_in_its_own_schema(tmp_path):
    state = corpus_path('US', 'US-CA', root=tmp_path)
    code = statute_corpus_path('US-CA', 'CIV', root=tmp_path)
    title = tmp_path / 'US' / 'cfr' / '24.sqlite'
    db = connect(state)
    db.execute("INSERT INTO section (pk, law_code, section_num, legal_text) VALUES ('1', 'CIV', '4000', 'state file')")
    db.commit()
    db.close()
    db = connect(code)
    db.execute("INSERT INTO section (pk, law_code, section_num, legal_text) VALUES ('1', 'CIV', '4000', 'civil file')")
    db.commit()
    db.close()
    db = connect(title)
    db.execute("INSERT INTO section (pk, law_code, section_num, legal_text) VALUES ('1', '24', '100.1', 'hud file')")
    db.commit()
    db.close()

    catalog = Catalog()
    assert catalog.attach_region('US-CA', root=tmp_path) == 'us_ca'
    assert catalog.attach_statute('US-CA', 'CIV', root=tmp_path) == 'us_ca_civ'
    assert catalog.attach_cfr(24, root=tmp_path) == 'cfr_24'
    assert catalog.attach(str(tmp_path / 'missing.sqlite'), 'missing') is None
    rows = {row[0]: row[3] for row in catalog.sections()}
    assert rows == {'us_ca': 'state file', 'us_ca_civ': 'civil file', 'cfr_24': 'hud file'}
    catalog.close()
    assert alias_for('US-CA') == 'us_ca'


def test_a_region_that_is_not_a_state_uses_its_code(tmp_path):
    class Zurich(Region):
        code = 'CH-ZH'

    assert corpus_path_for(Zurich, root=tmp_path).endswith('CH-ZH.sqlite')
    assert issubclass(UnitedStates, Country)
