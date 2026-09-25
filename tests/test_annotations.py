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
    constitution = heading_notes('SEC. 2. (Sec. 2 added Nov. 5, 1974, by Prop. 7.)')
    assert any(note.note is Note.CUT and note.target == 'section' and note.text == 'SEC.' for note in constitution)
    assert any(note.note is Note.CITATION and note.cite is Cite.SECTION and note.text == '2' for note in constitution)
    assert any(note.note is Note.DATE and note.target == '1974-11-05' for note in constitution)
    credit = heading_notes('SEC. 20. (Sec. 20 added Nov. 5, 1974, by Prop. 7. Res.Ch. 90, 1974.)')
    targets = [note.target for note in credit if note.note is Note.CITATION]
    assert 'prop 7' in targets
    assert 'res 90 1974' in targets
    assert any(note.cite is Cite.SECTION and note.text.lower().startswith('sec') for note in credit)


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


def test_a_quoted_term_that_means_is_a_definition():
    """GOV 12925. A curly-quoted term before means is the defined word."""
    text = Citation(Code.GOVERNMENT).section('12925').text
    if not text or 'means' not in text:
        return
    defined = [note for note in annotate(text) if note.note is Note.DEFINITION]
    targets = {note.target for note in defined}
    assert 'commission' in targets
    assert 'commissioner' in targets
    assert all(note.text.startswith('\u201c') and note.text.endswith('\u201d') for note in defined)
    defined_next = Citation(Code.GOVERNMENT).section('12926').text
    if defined_next and 'refers' in defined_next:
        targets = {note.target for note in annotate(defined_next) if note.note is Note.DEFINITION}
        assert 'age' in targets
        assert 'employee' in targets
        assert 'affirmative relief' in targets
        assert 'prospective relief' in targets
        assert 'limits' in targets
        assert 'major life activities' in targets
        compounds = {note.target for note in annotate(defined_next) if note.note is Note.COMPOUND}
        assert 'out-of-pocket' in compounds
        assert 'part-time' in compounds
        assert 'gender-related' in compounds


def test_a_public_law_number_is_not_a_code_section():
    """P.L. 101-336 is the 336th public law of the 101st Congress."""
    from parsers import Parser
    laws = Parser().public_laws('(P.L. 101-336)')
    assert laws[0].congress == '101'
    assert laws[0].number == '336'
    assert laws[0].target() == 'PL 101 336'
    assert laws[0].reference() == 'Public Law 101-336'
    assert laws[0].book() == '101-336'
    assert laws[0].shelf.value == 'public-law'
    marked = annotate('(P.L. 101-336)')
    assert marked[0].cite is Cite.BOOK
    assert marked[0].cite is not Cite.RANGE
    spelled = Parser().public_laws('Public Law 85-1')
    assert spelled[0].target() == 'PL 85 1'
    text = Citation(Code.GOVERNMENT).section('12926').text
    if text and 'P.L.' in text:
        notes = [note for note in annotate(text) if note.target == 'PL 101 336']
        assert notes
        assert notes[0].note is Note.CITATION
        acts = [note.text for note in annotate(text) if note.note is Note.NAMED_ACT]
        assert 'Americans with Disabilities Act of 1990' in acts


def test_an_act_title_beside_a_public_law_is_named():
    """The Act's name is a named act. The hyphenated number stays the book."""
    notes = annotate('the federal Americans with Disabilities Act of 1990 (P.L. 101-336)')
    act = next(note for note in notes if note.note is Note.NAMED_ACT)
    assert act.text == 'Americans with Disabilities Act of 1990'
    law = next(note for note in notes if note.cite is Cite.BOOK)
    assert law.target == 'PL 101 336'
    assert act.end <= law.start
    assert act.target == 'americans-with-disabilities'


def test_a_catalogued_act_is_marked_from_the_list():
    """The list is walked first. A title that is not on it still matches the grammar."""
    from parsers import Parser
    housed = annotate('The Fair Housing Act and the Nonprofit Mutual Benefit Corporation Law.')
    targets = {note.target for note in housed if note.note is Note.NAMED_ACT}
    assert targets == {'fair-housing', 'mutual-benefit'}
    unknown = annotate('the Synthetic Widgets Act of 1999')
    act = next(note for note in unknown if note.note is Note.NAMED_ACT)
    assert act.text == 'Synthetic Widgets Act of 1999'
    assert act.target == act.text
    listed = Parser().named_acts('Americans with Disabilities Act of 1990')
    assert listed[0][3] == 'americans-with-disabilities'
    assert 'of 1990' in listed[0][2]


def test_a_code_cite_is_not_the_public_law():
    """42 U.S.C. 12101 is the classified section. 104 Stat. 327 is the volume."""
    from parsers import Parser
    codes = Parser().federal_codes('the Act (42 U.S.C. 12101 et seq.)')
    assert codes[0].title == '42'
    assert codes[0].book() == '42'
    assert codes[0].shelf.value == 'code'
    assert codes[0].section == '12101'
    assert codes[0].target() == 'USC 42 12101'
    assert codes[0].text.endswith('et seq.')
    long = Parser().federal_codes('section 5 of title 15, United States Code')
    assert long[0].target() == 'USC 15 5'
    volume = Parser().statutes('104 Stat. 327')
    assert volume[0].target() == 'STAT 104 327'
    assert volume[0].book() == '104'
    assert volume[0].shelf.value == 'statutes'
    assert Parser().statutes('Stats. 2011, Ch. 719') == []
    notes = annotate('See 42 U.S.C. 12101 and section 5 of title 15, United States Code.')
    targets = {note.target for note in notes if note.note is Note.CITATION}
    assert 'USC 42 12101' in targets
    assert 'USC 15 5' in targets
    assert '5' not in targets
    assert all(note.cite is Cite.BOOK for note in notes if note.target in targets)


def test_a_quoted_roman_is_an_article():
    """Single quotes mark the numeral. The letter after it stays on the article."""
    from parsers import Parser
    nineteen = Parser().articles("'XIX'")
    assert nineteen[0].value == 'XIX'
    suffixed = Parser().articles("Article XIII A and 'XIX C'")
    assert [mark.value for mark in suffixed] == ['XIII A', 'XIX C']
    assert Parser().articles('A lone I in a sentence.') == []
    notes = annotate("See 'XIX' and Article I.")
    targets = {note.target for note in notes if note.note is Note.CITATION}
    assert 'CONS XIX' in targets
    assert 'CONS I' in targets
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
    short = Absolute.parse('Nov. 5, 1974')
    assert short.convention() is Convention.ABBREVIATED_MDY
    assert short.target() == '1974-11-05'
    assert Absolute.parse('Sept. 1, 1990').target() == '1990-09-01'
    added = annotate('Sec. 20 added Nov. 5, 1974, by Prop. 7.')
    assert any(note.note is Note.DATE and note.text == 'Nov. 5, 1974' and note.target == '1974-11-05' for note in added)
    assert Absolute.parse('Effective January 1, 2012') is None
    credit_notes = annotate('Effective January 1, 2012.')
    day = next(note for note in credit_notes if note.note is Note.DATE)
    cue = next(note for note in credit_notes if note.note is Note.OCCASION)
    assert day.text == 'January 1, 2012'
    assert day.target == '2012-01-01'
    assert cue.text == 'Effective'
    assert cue.target == day.target
    apart = annotate('Repealed as of January 1, 2015.')
    assert any(note.note is Note.DATE and note.text == 'January 1, 2015' for note in apart)
    assert any(note.note is Note.OCCASION and note.text == 'Repealed' and note.target == '2015-01-01' for note in apart)
    paired = {
        'Operative January 1, 1994.': ('Operative', '1994-01-01'),
        'Approved March 5, 2002.': ('Approved', '2002-03-05'),
        'Applicable from June 1, 1998.': ('Applicable', '1998-06-01'),
        'Superseded on July 1, 2005.': ('Superseded', '2005-07-01'),
    }
    for sentence, (word, day) in paired.items():
        notes = annotate(sentence)
        assert any(note.note is Note.OCCASION and note.text == word and note.target == day for note in notes)
        assert any(note.note is Note.DATE and note.target == day for note in notes)
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


def test_a_control_phrase_keeps_its_pairing():
    """The phrase and the object it controls are separate. The target is the object."""
    cases = (
        ('Notwithstanding any other provision of law, the rule applies.', Note.OVERRIDE, 'notwithstanding', 'any other provision'),
        ('Except as provided in Section 10, the rule applies.', Note.EXCEPTION, 'except as provided', 'in section'),
        ('Unless otherwise provided, the clerk files the paper.', Note.EXCEPTION, 'unless otherwise', 'provided'),
        ('Subject to Section 10, the board may act.', Note.LIMIT, 'subject to', 'section'),
        ('The board may act, provided that notice is given.', Note.PROVISO, 'provided that', 'proviso'),
    )
    for sentence, kind, words, target in cases:
        notes = annotate(sentence)
        found = next(note for note in notes if note.note is kind)
        assert found.text.casefold() == words
        assert found.target == target


def test_a_section_sign_is_a_citation_annotation():
    notes = annotate('See Bus. & Prof. Code § 10050.')
    citation = next(note for note in notes if note.note is Note.CITATION)
    assert '10050' in citation.target
    assert annotate('') == []
