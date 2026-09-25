from apa import Code
from places import Citation

from citations import Absolute, Cite, Convention, Duration, Monetary, Note, Quantity, annotate, find_durations, forms, frames
from structure import find_links


def test_internal_references_and_the_named_act_are_annotated():
    """BPC 10080. This part, commencing with Section 11000, and the Administrative Procedure Act."""
    rules = Citation(Code.BUSINESS_AND_PROFESSIONS).section('10080').text
    if 'Administrative Procedure Act' not in rules:
        return
    notes = annotate(rules)
    kinds = {note.note for note in notes}
    assert Note.CROSS_REFERENCE in kinds
    assert Note.NAMED_ACT in kinds
    assert any(note.text == 'commencing with Section 11000' for note in notes)
    assert any(note.text == 'Administrative Procedure Act' for note in notes)
    assert any(note.text == 'this part' for note in notes)


def test_a_part_heading_is_a_cut_under_the_division():
    """CIV 55.51. The heading names the part, and that part sits under the division."""
    import query
    body = query.section(Code.CIVIL, '55.51')
    if not body.get('found'):
        return
    levels = [step.get('level') for step in body.get('path') or []]
    assert 'division' in levels and 'part' in levels
    assert levels.index('part') > levels.index('division')
    from citations import heading_notes
    heading = next(step.get('heading') for step in body['path'] if step.get('level') == 'part')
    notes = heading_notes(heading)
    assert any(note.note is Note.CUT and note.target == 'part' for note in notes)
    ranged = next(note for note in notes if note.cite is Cite.RANGE)
    assert ranged.target.startswith('55.51-')
    division = heading_notes('DIVISION 1. PERSONS [38. - 86.]')
    span = next(note for note in division if note.cite is Cite.RANGE)
    assert span.target == '38-86'
    assert span.text == '[38. - 86.]'
    credit = heading_notes('55.51. (Added by Stats. 2008, Ch. 549, Sec. 3.)')
    assert any(note.note is Note.SESSION and note.target == 'added 2008 549' for note in credit)


def test_a_short_title_is_a_named_act():
    """CIV 55.51. The act introduced by 'may be cited as' is the named act, hyphen included."""
    text = Citation(Code.CIVIL).section('55.51').text
    if not text or 'may be cited' not in text.casefold():
        return
    notes = annotate(text)
    acts = [note.text for note in notes if note.note is Note.NAMED_ACT]
    assert any(name.endswith('Act') and '-' in name for name in acts)
    assert any(note.note is Note.CROSS_REFERENCE and note.text.casefold() == 'this part' for note in notes)


def test_house_units_and_as_amended_are_annotated():
    """HOLC guide: this Act, and a citation as amended. Water Code section 12872: subsection of another section."""
    guide = open('docs/lexical/sources/holc-guide.md', encoding='utf-8').read()
    notes = annotate(guide)
    assert any(note.text.lower() == 'this act' for note in notes)
    assert any(note.note is Note.SHORT_FORM and note.text.lower() == 'as amended' for note in notes)
    water_text = Citation(Code.WATER).section('12872').text
    if not water_text:
        return
    water = annotate(water_text)
    named = next(note for note in water if (note.target or '').endswith('12867(d)'))
    assert named.note is Note.CROSS_REFERENCE
    assert named.target.endswith('12867(d)')


def test_an_added_or_amended_credit_keeps_the_action():
    """The history verb is the action. Stats. year and chapter stay the session law."""
    from needles import Action
    added = annotate('Added by Stats. 2011, Ch. 383, Sec. 2.')
    note = next(item for item in added if item.note is Note.SESSION)
    assert note.target == 'added 2011 383'
    assert note.text.lower().startswith('added by stats.')
    amended = find_links('Amended by Stats. 1987, Ch. 56, Sec. 4.')
    credit = next(link for link in amended if link.kind == 'session')
    assert credit.action is Action.AMENDED
    assert credit.session.target() == '1987 56'


def test_a_session_chapter_is_not_a_code_chapter():
    """WAT 38500. Chapter 387 of the Statutes of 1913 is a session law. The target is year, then chapter."""
    text = Citation(Code.WATER).section('38500').text
    if 'Statutes of' not in text:
        return
    notes = annotate(text)
    session = next(note for note in notes if note.note is Note.SESSION)
    assert session.target == '1913 387'
    assert not any(note.note is Note.CITATION and note.target == '1913 387' for note in notes)


def test_a_cut_records_a_definition_and_a_reference():
    """The breakdown word is the target. A definition target ends in means."""
    notes = annotate('Subdivision means a subdivision of the section. See subdivision (a).')
    cuts = [note for note in notes if note.note is Note.CUT]
    assert any(note.target == 'subdivision means' for note in cuts)
    assert any(note.target == 'subdivision' and note.text.lower().endswith('(a)') for note in cuts)
    text = Citation(Code.GOVERNMENT).section('10').text
    if not text:
        return
    defined = [note for note in annotate(text) if note.note is Note.CUT]
    assert any(note.target == 'subdivision means' for note in defined)
    insurance = Citation(Code.INSURANCE).section('10').text
    if insurance:
        targets = {note.target for note in annotate(insurance) if note.note is Note.CUT}
        assert 'subdivision' in targets
        assert 'subsection means' in targets
    water = Citation(Code.WATER).section('12872').text
    if water:
        links = find_links(water, here=Code.WATER)
        assert any(
            link.kind == 'subdivision' and link.label == 'd' and link.section == '12867'
            for link in links
        )
        assert any(
            note.note is Note.CUT and note.target == 'subsection' for note in annotate(water)
        )


def test_frequent_and_rare_marks_keep_their_shape():
    """Shapes counted across the codes: a shared period, a one-code period, a large sum, and a short form in either case."""
    assert Duration.parse('1 year').target() == '1 year'
    assert Duration.parse('6 months').target() == '6 month'
    assert Duration.parse('within 30 days').target() == 'within 30 day'
    assert Duration.parse('39 months').target() == '39 month'
    assert Duration.parse('1 business day after').target() == '1 business day after'
    assert Duration.parse('prior to 7 years from').target() == 'prior to 7 year from'
    assert Duration.parse('50,000 years').target() == '50000 year'
    assert Duration.parse('50,000 years').shape() == 'duration year'
    assert Duration.parse('within 30 days').shape() == 'within duration day'
    assert Duration.parse('within 95 days').shape() == 'within duration day'
    assert Duration.parse('1 business day after').shape() == 'duration business day after'
    assert Monetary.parse('$1,000').shape() == 'monetary'
    assert Monetary.parse('$10,000').shape() == 'monetary'
    assert Absolute.parse('January 1, 2013').shape() == 'absolute'
    assert Monetary.parse('$1,000').dollars == 1000
    assert Monetary.parse('$10,000').dollars == 10000
    assert Monetary.parse('$489,900,000').dollars == 489900000
    assert Monetary.parse('$1,234.56').target() == '1234.56'
    assert Monetary.parse('$.50').target() == '0.50'
    assert Monetary.parse('$1.5').target() == '1.50'
    assert Monetary.parse('$1.234').target() == '1.234'
    assert Monetary.parse('1,234.56 dollars').dollars == 1234
    fine = frames('The court may impose a fine of not more than $1,000.')
    same = frames('The court may impose a fine of not more than $10,000.')
    assert fine == same
    assert fine == ['not more than monetary']
    due = frames('The notice is due within 30 days.')
    later = frames('The notice is due within 95 days.')
    assert due == later
    assert 'within duration day' in due[0]
    shouted = annotate('See Section 100 et seq. and the act ET SEQ. As amended.')
    forms = [note for note in shouted if note.note is Note.SHORT_FORM]
    assert any(note.text == 'et seq.' and note.target == 'et seq.' for note in forms)
    assert any(note.text == 'ET SEQ.' and note.target == 'et seq.' for note in forms)
    assert any(note.text == 'As amended' and note.target == 'as amended' for note in forms)
    cuts = [note.target for note in annotate('A subitem (aa) follows.') if note.note is Note.CUT]
    assert 'subitem' in cuts
    series = [note for note in annotate('paragraph (1), (2), or (3)') if note.note is Note.CUT]
    assert series[0].text == 'paragraph (1), (2), or (3)'
    assert series[0].target == 'paragraph'


def test_a_dollar_amount_and_a_period_are_annotated():
    """The amount and the period are elements of the clause, not the clause itself."""
    notes = annotate('The fee is $100,000, payable within 10 calendar days.')
    amount = next(note for note in notes if note.note is Note.AMOUNT)
    period = next(note for note in notes if note.note is Note.PERIOD)
    assert amount.text == '$100,000'
    assert amount.target == '100000'
    assert period.target == 'within 10 calendar day'
    assert Duration.parse('within 10 days after').reference() == 'within 10 days after'
    assert Duration.parse('30 days from').reference() == '30 days from'
    assert Duration.parse('30 days prior to').reference() == '30 days prior to'
    assert Duration.parse('prior to 30 days').lead == 'prior to'
    heard = find_durations('Notice is due 30 days from the hearing.')
    assert heard[0].antecedent == 'the hearing'
    assert heard[0].reference() == '30 days from the hearing'
    assert Monetary.parse('$100,000').reference() == 'one hundred thousand dollars ($100,000)'
    assert Monetary.parse('one hundred thousand dollars ($100,000)').dollars == 100000
    assert Monetary.parse('ten thousand dollars ($10,000)').dollars == 10000
    parent = Citation(Code.CIVIL).section('1714.1').text
    assert parent
    sums = [note.target for note in annotate(parent) if note.note is Note.AMOUNT]
    assert '10000' in sums
    assert '25000' in sums
    phrase = Citation(Code.GOVERNMENT).section('53895').containing(
        'one hundred thousand dollars',
    )
    if phrase:
        amounts = [note for note in annotate(phrase) if note.note is Note.AMOUNT]
        assert any(note.target == '100000' and 'dollars' in note.text for note in amounts)
    assert Duration.parse('10 calendar days').reference() == '10 calendar days'
    assert Absolute.parse('January 1, 2020').reference() == 'January 1, 2020'
    assert Absolute.parse('January 1, 2020').kind is Quantity.ABSOLUTE
    dated = annotate('This section becomes operative on January 1, 2020.')
    day = next(note for note in dated if note.note is Note.DATE)
    assert day.target == '2020-01-01'
    assert day.text == 'January 1, 2020'
    looked = Citation(Code.CIVIL).section('8830').containing('within 10 days')
    if not looked:
        return
    found = annotate(looked)
    assert any(
        note.note is Note.PERIOD and note.target.startswith('within 10 day')
        for note in found
    )


def test_a_grouped_year_count_is_one_period():
    """50,000 years is one period. The trailing group is not a period of zero."""
    text = Citation(Code.GOVERNMENT).section('425.9').text
    assert text
    periods = [note for note in annotate(text) if note.note is Note.PERIOD]
    assert any(note.target == '250000 year' for note in periods)
    assert all(note.target != '0 year' for note in periods)
    common = Citation(Code.BUSINESS_AND_PROFESSIONS).section('23451').text
    rare = Citation(Code.GOVERNMENT).section('68115').text
    assert any(Duration.parse(note.text).shape() == 'duration year' for note in annotate(common) if note.note is Note.PERIOD)
    assert any(Duration.parse(note.text).shape() == 'from duration court day' for note in annotate(rare) if note.note is Note.PERIOD)


def test_case_notes_keep_uppercase_and_title_case():
    titled = annotate('The Department of Real Estate acts today.')
    assert any(note.note is Note.CASE and note.target == 'title' and 'Department of Real Estate' in note.text for note in titled)
    shouted = annotate('The board meets in CALIFORNIA today.')
    assert any(note.note is Note.CASE and note.target == 'uppercase' and note.text == 'CALIFORNIA' for note in shouted)


def test_each_format_records_its_convention():
    """USD, a grouped decimal, a printed day, an ISO day, and a period designator."""
    money = Monetary.parse('$1,234.56')
    assert Convention.USD in money.convention()
    assert Convention.GROUPED in money.convention()
    assert Convention.DECIMAL in money.convention()
    spelled = Monetary.parse('one hundred thousand dollars ($100,000)')
    assert Convention.SPELLED in spelled.convention()
    assert Convention.USD in spelled.convention()
    named = Absolute.parse('January 1, 2013')
    assert named.convention() is Convention.MONTH_DAY_YEAR
    assert named.target() == '2013-01-01'
    assert Absolute.parse('2013-01-01').convention() is Convention.ISO_8601
    assert Absolute.parse('2013-01-01').target() == '2013-01-01'
    numeric = Absolute.parse('1/1/2013')
    assert numeric.convention() is Convention.NUMERIC_MDY
    assert numeric.target() == '2013-01-01'
    assert Absolute.parse('2013-13-01') is None
    assert Duration.parse('30 days').convention() is Convention.DAY
    assert Duration.parse('1 year').convention() is Convention.YEAR
    from parsers import Parser
    found = Parser().formats('pay $1,000 on January 1, 2013 or on 2013-01-02 within 30 days')
    kinds = {item.kind for item in found}
    assert Quantity.MONETARY in kinds
    assert Quantity.ABSOLUTE in kinds
    assert Quantity.DURATION in kinds
    assert any(Convention.ISO_8601 in item.conventions for item in found)
    assert forms('pay $1,000.')[0].kind is Quantity.MONETARY


def test_a_section_sign_is_a_citation_annotation():
    notes = annotate('See Bus. & Prof. Code § 10050.')
    citation = next(note for note in notes if note.note is Note.CITATION)
    assert '10050' in citation.target
    assert annotate('') == []
