"""Scoped term weights. The math does not need the index. The rank does."""

from weight import (
    Noted, Scope, Surface, Weight, _by_common, _term_set, by_cut, ends, idf_weight, mark_term,
    glance, needle_weights, rollup, shape_term, successive, tf_weight, useful_needles,
)


def test_a_hovered_term_counts_its_neighbors_in_the_rows():
    """The popup uses the hits in hand. The pair beside the term keeps its count."""
    rows = (
        ('CIV', 'The court shall not impose a fine.'),
        ('FGC', 'The board shall not delay the hearing.'),
        ('GOV', 'A fine of one hundred dollars.'),
    )
    found = glance('shall', rows)
    assert found['found'] is True
    assert found['df'] == 2
    assert found['pf'] == 2
    phrases = {item['phrase']: item['pf'] for item in found['neighbors']}
    assert phrases['court shall'] == 1
    assert phrases['shall not'] == 2
    assert glance('', rows)['found'] is False


def test_a_heading_count_stays_apart_from_the_body():
    """PART on a heading is not another body hit for the same cut."""
    rows = (
        ('CIV', 'cut', 'PART', 'part', 'heading'),
        ('CIV', 'cut', 'PART', 'part', 'heading'),
        ('GOV', 'cut', 'PART', 'part', 'heading'),
        ('CIV', 'cut', 'part', 'part'),
    )
    body = Scope.CODE('CIV').marks('cut', rows)
    headings = Scope.CODE('CIV').headings('cut', rows)
    assert [(item.term, item.af) for item in body] == [('part', 1)]
    assert [(item.term, item.af) for item in headings] == [('part', 2)]
    assert headings[0].surface is Surface.HEADING
    assert body[0].surface is Surface.BODY


def test_a_rare_code_term_outranks_a_shared_one():
    rare = tf_weight(40) * idf_weight(1, 29)
    shared = tf_weight(400) * idf_weight(29, 29)
    assert rare > shared


def test_one_posting_pass_rolls_a_section_into_every_scope():
    """Two chapters of one code. The code total is the sum. The chapter df is two."""
    fish = {Scope.CODE: 'FGC', Scope.CHAPTER: 'FGC 1', Scope.ARTICLE: 'FGC 2'}
    also = {Scope.CODE: 'FGC', Scope.CHAPTER: 'FGC 2', Scope.ARTICLE: 'FGC 2'}
    other = {Scope.CODE: 'CIV', Scope.CHAPTER: 'CIV 1', Scope.ARTICLE: 'CIV 1'}
    totals = rollup(((fish, 3), (also, 4), (other, 10)))
    assert totals[Scope.CODE]['FGC'] == 7
    assert totals[Scope.CODE]['CIV'] == 10
    assert totals[Scope.CHAPTER]['FGC 1'] == 3
    assert len(totals[Scope.CHAPTER]) == 3
    assert totals[Scope.ARTICLE]['FGC 2'] == 7


def test_a_scope_closes_over_its_member():
    """Scope.CODE('FGC').take(5) remembers the code and the limit."""
    lex = Scope.CODE('FGC').take(5)
    assert lex.scope is Scope.CODE
    assert lex.key == 'FGC'
    assert lex.limit == 5


def test_common_puts_the_shared_term_ahead_of_the_rare_one():
    """The inverse of rank. The term in every code comes first."""
    rare = Weight(Scope.CODE, 'FGC', 'smelt', 40, 1, idf_weight(1, 29), 9.0)
    shared = Weight(Scope.CODE, 'FGC', 'shall', 400, 29, idf_weight(29, 29), 1.0)
    ordered = _by_common([rare, shared], 2)
    assert ordered[0].term == 'shall'
    assert ordered[1].term == 'smelt'
    assert ordered[:1][0].term == 'shall'
    assert _term_set((rare, shared)) == frozenset({'shall', 'smelt'})


def test_an_identified_amount_stays_a_term():
    """A dollar amount is digits. The token lexicon drops it. The mark keeps it."""
    assert mark_term('amount', '$10,000', '10000') == '10000'
    assert mark_term('case', 'SMELT', 'uppercase') == 'smelt'
    rows = (
        ('FGC', 'amount', '$10,000', '10000'),
        ('FGC', 'amount', '$10,000', '10000'),
        ('CIV', 'amount', '$100', '100'),
        ('FGC', 'case', 'SMELT', 'uppercase'),
    )
    ranked = Scope.CODE('FGC').marks('amount', rows)
    assert ranked[0].term == '10000'
    assert ranked[0].af == 2
    assert ranked[0].note == 'amount'
    assert ranked[0].scope is Scope.CODE
    assert ranked[0].key == 'FGC'
    assert all(item.term != '100' for item in ranked)
    chapters = (
        ('FGC 1', 'amount', '$10,000', '10000'),
        ('FGC 2', 'amount', '$10,000', '10000'),
        ('FGC 2', 'amount', '$100', '100'),
    )
    chapter = Scope.CHAPTER('FGC 1').marks('amount', chapters)
    assert chapter[0].term == '10000'
    assert chapter[0].af == 1
    assert chapter[0].df == 2
    assert chapter[0].scope is Scope.CHAPTER
    state = Scope.STATE('US-CA').marks('amount', (('US-CA', 'amount', '$10,000', '10000'),))
    assert state[0].idf == 0.0
    assert Scope.FEDERAL('US').marks('amount', rows) == []


def test_a_quantity_phrase_counts_without_the_number():
    """within 30 days and within 95 days are one phrase. The mark keeps the count."""
    assert shape_term('period', 'within 30 days') == 'within duration day'
    assert shape_term('period', 'within 95 days') == 'within duration day'
    assert shape_term('amount', '$1,000') == 'monetary'
    assert shape_term('citation', 'Section 16460') is None
    assert mark_term('period', 'within 95 days', 'within 95 day') == 'within 95 day'
    rows = (
        ('FGC', 'period', 'within 30 days', 'within 30 day'),
        ('CIV', 'period', 'within 95 days', 'within 95 day'),
        ('FGC', 'period', 'prior to 7 years from', 'prior to 7 year from'),
    )
    ranked = Scope.CODE('FGC').shapes('period', rows)
    shared = next(item for item in ranked if item.term == 'within duration day')
    assert shared.af == 1
    assert shared.df == 2
    assert any(item.term == 'prior to duration year from' for item in ranked)


def test_successive_pairs_carry_a_count():
    """One pass. Each overlapping pair keeps how often it occurred."""
    sentence = 'A quick brown fox jumped over the lazy dog'
    once = successive((('FGC', sentence),))
    counts = {item.phrase: (item.pf, item.df) for item in once}
    assert len(once) == 8
    assert counts['a quick'] == (1, 1)
    assert counts['quick brown'] == (1, 1)
    assert counts['brown fox'] == (1, 1)
    assert counts['lazy dog'] == (1, 1)
    twice = successive((('FGC', sentence), ('CIV', sentence)))
    shared = {item.phrase: (item.pf, item.df) for item in twice}
    assert shared['fox jumped'] == (2, 2)


def test_an_annotated_value_is_a_placeholder_in_the_pair():
    """The printed pair and the placeholder pair each keep their own count."""
    sentence = 'See Section 813, Civil Code and pay $1,000.'
    counts = {item.phrase: item.pf for item in successive((('CIV', sentence),))}
    assert counts['section {SECTION}'] == 1
    assert counts['{SECTION} {CODE}'] == 1
    assert counts['pay {AMOUNT}'] == 1
    assert counts['section 813'] == 1
    assert counts['civil code'] == 1
    assert counts['pay $1,000'] == 1
    assert counts['see section'] == 1
    dated = {item.phrase: item.pf for item in successive((('CIV', 'operative on January 1, 2013.'),))}
    assert dated['on {YEAR}'] == 1
    assert dated['january 1'] == 1


def test_shared_neighbors_grow_into_the_whole_phrase():
    """The word on each side is a pair. The shared run is the phrase."""
    rows = (
        ('FGC', 'The court may impose a fine of not more than $1,000.'),
        ('CIV', 'The court may impose a penalty of not more than $10,000.'),
    )
    grown = Scope.CODE('FGC').extend(rows, 'monetary')
    assert grown.phrase == 'of not more than monetary'
    assert grown.before == ('of', 'not', 'more', 'than')
    assert grown.after == ()
    assert Scope.CODE('EVID').extend(rows, 'monetary') is None


def test_the_scope_slides_until_the_members_split():
    """Shared words stay. The walk stops where the codes disagree."""
    rows = (
        ('FGC', 'a fine of not more than one'),
        ('CIV', 'a penalty of not more than one'),
    )
    grown = Scope.CODE('FGC').hunt(rows, 'not more than')
    assert grown.phrase == 'of not more than one'
    assert grown.distance == 2
    assert grown.support == 2
    assert Scope.CODE('EVID').hunt(rows, 'not more than') is None


def test_a_phrase_search_grows_until_the_codes_split(tmp_path):
    """Positions come from a small index. The live catalog is not opened."""
    from indexer import Indexer
    idxer = Indexer(tmp_path / 'idx')
    laws = [
        {
            'PK': '2025:fgc1',
            'LAW_CODE': 'FGC',
            'SECTION_NUM': '1',
            'CODE_HEADING': 'Fish and Game Code - FGC',
            'LEGAL_TEXT': 'The fine imposed before judgment today.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
            'SUBDIVISION': 'US-CA',
        },
        {
            'PK': '2025:civ1',
            'LAW_CODE': 'CIV',
            'SECTION_NUM': '1',
            'CODE_HEADING': 'Civil Code - CIV',
            'LEGAL_TEXT': 'The penalty imposed before judgment later.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
            'SUBDIVISION': 'US-CA',
        },
    ]
    idxer.index_pubinfo_laws(str(tmp_path / 'pub.zip'), laws)
    grown = idxer.hunt('imposed before')
    assert grown is not None
    assert grown.phrase == 'impos befor judgment'
    assert grown.distance == 1


def test_the_same_words_around_a_sum_count_once():
    rows = (
        ('FGC', 'A fine of not more than $1,000.'),
        ('CIV', 'A fine of not more than $10,000.'),
        ('FGC', 'The notice is due within 30 days.'),
    )
    ranked = Scope.CODE('FGC').frames(rows)
    fine = next(item for item in ranked if item.term == 'not more than monetary')
    assert fine.af == 1
    assert fine.df == 2


def test_annotation_frequency_aggregates_by_cut():
    rows = (
        ('FGC', 'cut', 'subdivision (a)', 'subdivision'),
        ('FGC', 'cut', 'subdivision (b)', 'subdivision'),
        ('CIV', 'cut', 'paragraph (1)', 'paragraph'),
        ('FGC', 'amount', '$10,000', '10000', 'subdivision'),
        ('CIV', 'amount', '$100', '100', 'paragraph'),
    )
    labels = by_cut(rows, 'cut')
    assert labels['subdivision'][0].af == 2
    assert labels['paragraph'][0].af == 1
    amounts = Scope.CODE('FGC').cuts(rows, 'amount')
    assert amounts['subdivision'][0].term == '10000'
    assert amounts['subdivision'][0].scope is Scope.CODE
    assert amounts['paragraph'] == []
    divided = Scope.DIVISION('FGC 1').cuts(
        (('FGC 1', 'amount', '$10,000', '10000', 'subdivision'),),
        'amount',
    )
    assert divided['subdivision'][0].key == 'FGC 1'
    assert divided['subdivision'][0].scope is Scope.DIVISION


def test_a_closed_list_keeps_unique_rows_and_a_flag():
    """``where`` keeps a flag. ``unique`` keeps the first row for each phrase."""
    rows = (
        ('FGC', 'may not act'),
        ('CIV', 'may not act'),
        ('WAT', 'smelt run'),
    )
    documented = Scope.CODE('FGC').document(rows)
    assert [item.text for item in documented.where('expression')] == ['may not']
    assert [item.text for item in documented.without('expression').where('useful')] == ['not act']
    assert documented.where('useful').descending('df').top(1)[0].text == 'may not'
    repeated = ends(list(documented) + list(documented)).unique()
    assert len(repeated) == len(documented)


def test_top_and_bottom_read_the_ends_of_an_ordered_list():
    """``top`` is the start of the order. ``bottom`` is the end. Neither is a heading."""
    rows = (
        ('FGC', 'may not act'),
        ('CIV', 'may not act'),
        ('WAT', 'smelt run'),
    )
    documented = Scope.CODE('FGC').document(rows)
    assert documented.top(1)[0].text == 'may not'
    assert documented.bottom(1)[0].text == 'smelt run'
    assert documented.top(0) == []
    assert ends(documented).bottom(2)[0].text == 'not act'


def test_a_phrase_is_documented_with_the_scopes_that_use_it():
    """A shared pair is useful. A pair in one member is relevant there only."""
    rows = (
        ('FGC', 'may not act'),
        ('CIV', 'may not act'),
        ('WAT', 'smelt run'),
    )
    found = {item.text: item for item in Scope.CODE('FGC').document(rows)}
    assert found['may not'].expression
    assert found['may not'].useful
    assert found['may not'].members == frozenset({'FGC', 'CIV'})
    assert found['may not'].scope is Scope.CODE
    assert not found['smelt run'].useful
    assert found['smelt run'].members == frozenset({'WAT'})
    chapters = Scope.CHAPTER('FGC 1').document((
        ('FGC 1', 'may not act'),
        ('FGC 2', 'smelt run'),
        ('FGC 3', 'smelt run'),
    ))
    by_text = {item.text: item for item in chapters}
    assert by_text['may not'].scope is Scope.CHAPTER
    assert by_text['may not'].members == frozenset({'FGC 1'})
    assert not by_text['may not'].useful


def test_adjacent_words_are_counted_as_a_phrase():
    """``may not`` is already an expression. A shared pair outranks a pair in one code."""
    rows = (
        ('FGC', 'the board may not act'),
        ('FGC', ('may', 'not')),
        ('CIV', 'the board may not meet'),
    )
    found = {item.phrase: item for item in Scope.CODE('FGC').pairs(rows)}
    assert found['may not'].pf == 2
    assert found['may not'].df == 2
    assert found['may not'].expression
    assert found['board may'].pf == 1
    assert not found['board may'].expression
    assert 'not meet' not in found


def test_needles_are_counted_apart_from_other_terms():
    """A form is counted. ``this`` plus a form counts as the form. Another word is left out."""
    rows = (
        ('FGC', 'shall'),
        ('FGC', 'shall'),
        ('FGC', 'this section'),
        ('FGC', 'smelt'),
        ('CIV', 'shall'),
    )
    counted = Scope.CODE('FGC').needle_count(rows)
    by_term = {item.term: item for item in counted}
    assert by_term['shall'].nf == 2
    assert by_term['shall'].df == 2
    assert by_term['section'].nf == 1
    assert 'smelt' not in by_term
    assert needle_weights(rows, scope=Scope.CHAPTER, key='FGC 1') == []


def test_a_shared_unmatched_word_is_a_needle_candidate():
    """A form, and this plus a form, are already needles. A rare word stays a weight."""
    weights = (
        Noted('cross_reference', 'this section', 10, 30, 1.0, 1.0),
        Noted('cross_reference', 'the hearing', 8, 20, 1.0, 1.0),
        Noted('amount', '1000', 15, 30, 1.0, 1.0),
        Noted('antecedent', 'the filing', 4, 1, 3.0, 3.0),
    )
    found = useful_needles(weights, n=30)
    assert [item.term for item in found['needles']] == ['this section']
    assert [item.term for item in found['candidates']] == ['the hearing']
    assert [item.term for item in found['quantities']] == ['1000']
    assert [item.term for item in found['distinctive']] == ['the filing']


def test_one_state_has_no_contrast():
    assert idf_weight(1, 1) == 0.0
    assert Scope.STATE.value == 'state'
    assert Scope.FEDERAL.value == 'federal'
