from mentions import Kind, abbreviations, find_mentions


TEXT = """
The people of the State of California do enact as follows.
The City of Sacramento sits in the County of Sacramento.
The Superior Court of the State of California, County of Sacramento hears the case.
The Department of Real Estate acts under its statute.
The State of Atlantis has no code here.
"""


def test_a_short_form_is_introduced_beside_the_name():
    text = 'The Department of Real Estate (DRE) shall act. The DRE may publish forms.'
    rows = abbreviations(text)
    intro = next(row for row in rows if row.introduction)
    assert intro.short == 'DRE'
    assert intro.name == 'Department of Real Estate'
    assert any(not row.introduction and row.name == intro.name and row.short == 'DRE' for row in rows)
    quoted = abbreviations('The Department of Real Estate (hereinafter "DRE") remains the DRE.')
    assert quoted[0].introduction
    assert quoted[0].short == 'DRE'
    assert any(not row.introduction for row in quoted)


def test_frames_classify_without_a_name_list():
    kinds = {(mention.kind, mention.name) for mention in find_mentions(TEXT)}
    assert (Kind.STATE, 'California') in kinds
    assert (Kind.CITY, 'Sacramento') in kinds
    assert (Kind.COUNTY, 'Sacramento') in kinds
    assert (Kind.STATE, 'Atlantis') in kinds


def test_known_state_resolves_to_its_code():
    california = next(
        mention for mention in find_mentions(TEXT)
        if mention.kind is Kind.STATE and mention.name == 'California'
    )
    atlantis = next(
        mention for mention in find_mentions(TEXT)
        if mention.name == 'Atlantis'
    )
    assert california.code == 'US-CA'
    assert atlantis.kind is Kind.STATE
    assert atlantis.code is None


def test_city_and_county_resolve_when_registered():
    city = next(mention for mention in find_mentions(TEXT) if mention.kind is Kind.CITY)
    county = next(mention for mention in find_mentions(TEXT) if mention.kind is Kind.COUNTY)
    assert city.code == 'Sacramento'
    assert county.code == 'US-CA'


def _dre():
    """BPC 10050, sliced to the sentence that creates the department."""
    import query
    from apa import Code
    return query.excerpt(Code.BUSINESS_AND_PROFESSIONS, '10050', 'Department of Real Estate')


def test_roster_name_is_also_searched_in_statute_order():
    from mentions import name_queries
    assert name_queries('Real Estate, Department of (DRE)') == [
        'Real Estate, Department of (DRE)',
        'Department of Real Estate',
    ]


def _duty():
    """BPC 10050, 10071, and 10080. Each duty sentence is sliced from its section."""
    import query
    from apa import Code
    pins = (
        ('10050', 'principal responsibility'),
        ('10071', 'shall enforce the provisions'),
        ('10071', 'full power'),
        ('10080', 'may adopt'),
        ('10080', 'Administrative Procedure Act'),
    )
    parts = [
        query.excerpt(Code.BUSINESS_AND_PROFESSIONS, number, phrase)
        for number, phrase in pins
    ]
    return '\n'.join(part for part in parts if part)


def test_duty_phrases_mark_responsibility_power_and_scope():
    from mentions import Relation, find_relations
    text = _duty()
    if not text:
        return
    found = {tie.relation for tie in find_relations(text)}
    assert Relation.RESPONSIBILITY in found
    assert Relation.DUTY in found
    assert Relation.POWER in found
    assert Relation.PROCEDURE in found
    assert Relation.SCOPE in found
    assert find_relations('') == []


def test_succession_vests_the_office():
    """GOV 12802. The agency shall succeed to, and is vested with, the prior duties."""
    import query
    from apa import Code
    from mentions import find_enactments
    text = query.section(Code.GOVERNMENT, '12802').get('text') or ''
    if not text:
        return
    frames = {mark.name for mark in find_enactments(text)}
    assert 'vesting' in frames


def test_an_ordinance_ordains():
    """ELEC 9224. The people of the city do ordain as follows."""
    import query
    from apa import Code
    from lexical import Clause, find_clauses
    text = query.section(Code.ELECTIONS, '9224').get('text') or ''
    if not text:
        return
    assert any(mark.clause is Clause.ENACTMENT for mark in find_clauses(text))


def test_enactment_frames_in_the_real_estate_statute():
    from mentions import find_enactments
    text = _dre()
    if not text:
        return
    frames = {mark.name for mark in find_enactments(text)}
    assert 'establishment' in frames
    assert 'officer' in frames
    assert find_enactments('') == []


def test_court_and_agency_frames():
    court = next(mention for mention in find_mentions(TEXT) if mention.kind is Kind.COURT)
    agency = next(mention for mention in find_mentions(TEXT) if mention.kind is Kind.AGENCY)
    assert court.name == 'Sacramento'
    assert 'Department of Real Estate' in agency.text
    assert find_mentions('') == []
