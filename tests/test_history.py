"""Section history across the shelf's editions, and the recodification readings.

The notes and table lines below are composed from parts (an action, a
year, a chapter); no statute sentence is copied here. Tests that read the
shelf or the Commission's documents skip when those are not on disk.
"""

import pytest

import history
import succession
from history import Change, Edition, compare, read_note, step
from needles import Action, Occasion
from succession import Provision, Report, Source, Succession


def _note(action, year, chapter, act, bill='', effective=None, operative=None):
    parts = ['%s by Stats. %s, Ch. %s, Sec. %s.' % (action, year, chapter, act)]
    if bill:
        parts.append('(%s)' % bill)
    if effective:
        parts.append('Effective %s.' % effective)
    if operative:
        parts.append('Operative %s, by Sec. 3 of Ch. %s.' % (operative, chapter))
    return '   '.join(parts)


def test_a_note_reads_into_its_action_statute_bill_and_days():
    note = read_note(_note('Added', 2012, 180, 2, 'AB 805', 'January 1, 2013', 'January 1, 2014'))
    assert note.read
    assert note.action is Action.ADDED
    assert (note.statute.year, note.statute.chapter, note.statute.act) == ('2012', '180', '2')
    assert note.bill == 'AB 805'
    assert note.effective == '2013-01-01'
    assert note.operative == '2014-01-01'
    assert note.citation() == 'Stats. 2012, Ch. 180, Sec. 2'
    assert [dated.occasion for dated in note.dates] == [Occasion.EFFECTIVE, Occasion.OPERATIVE]


def test_the_act_a_note_names_is_after_its_as_amended_parenthetical():
    text = 'Amended (as amended by Stats. 1990, Ch. 10, Sec. 1) by Stats. 1991, Ch. 20, Sec. 2.'
    note = read_note(text)
    assert note.action is Action.AMENDED
    assert note.statute.year == '1991' and note.statute.chapter == '20'


def test_renumbering_keeps_the_former_number():
    note = read_note('Added by renumbering Section 100.5 by Stats. 1997, Ch. 17, Sec. 16.')
    assert note.action is Action.RENUMBERED
    assert note.source == '100.5'


def test_an_unknown_note_stays_unread_and_keeps_its_words():
    note = read_note('See note.')
    assert not note.read
    assert note.note == 'See note.'


def test_a_bill_label_is_not_part_of_the_act():
    plain = read_note(_note('Amended', 2013, 183, 14, effective='January 1, 2014'))
    labelled = read_note(_note('Amended', 2013, 183, 14, 'SB 745', 'January 1, 2014'))
    assert plain.identity() == labelled.identity()


def test_compare_counts_words_and_names_the_cut_before_each_hunk():
    diff = compare('(a) alpha beta gamma (b) delta epsilon', '(a) alpha beta gamma (b) delta zeta eta')
    assert diff.replaced == 2 or (diff.inserted, diff.replaced) == (1, 1)
    assert diff.hunks[0].near == '(b)'
    assert 0 < diff.ratio < 1
    assert 'near (b)' in diff.summary()


def _edition(session, words, note):
    return Edition(session=session, found=True, digest=history.digest(words), words=len(words.split()),
                   credit=read_note(note), text=words)


def test_a_step_says_added_amended_revised_renoted_unchanged_or_repealed():
    first = _note('Added', 2012, 180, 2, effective='January 1, 2013')
    later = _note('Amended', 2025, 22, 4, 'AB 130', 'June 30, 2025')
    absent = Edition(session='2011', found=False, reason='not_in_edition')
    assert step('CIV', '9', absent, _edition('2013', 'one two', first)).change is Change.ADDED
    assert step('CIV', '9', _edition('2023', 'one two', first),
                _edition('2025', 'one two three', later)).change is Change.AMENDED
    assert step('CIV', '9', _edition('2015', 'one two', first),
                _edition('2017', 'one three', first)).change is Change.REVISED
    labelled = _note('Added', 2012, 180, 2, 'AB 805', 'January 1, 2013')
    assert step('CIV', '9', _edition('2015', 'one two', first),
                _edition('2017', 'one two', labelled)).change is Change.RENOTED
    assert step('CIV', '9', _edition('2017', 'one two', labelled),
                _edition('2019', 'one two', labelled)).change is Change.UNCHANGED
    gone = Edition(session='2013', found=False, reason='not_in_edition')
    assert step('XYZ', '9', _edition('2011', 'one two', first), gone).change is Change.REPEALED


def test_a_table_line_reads_into_a_row():
    rows = succession.read_pdf_table(
        '1111(e)(3) (except last ¶)....................... 4444, 4445(a)-(b), (d)\n'
        '1112 ............................................ omitted, but see 4446, 4447\n'
        '1113(b) ......................................... omitted\n',
        'CIV', 'test', Report.AB805_DISPOSITION,
    )
    first, second, third = rows
    assert first.former.section == '1111' and first.former.path == ('e', '3')
    assert [target.label() for target in first.targets] == ['4444', '4445(a)-(b)', '4445(d)']
    assert first.succession is Succession.CONTINUED and first.source is Source.DISPOSITION_TABLE
    assert second.succession is Succession.OMITTED_SEE
    assert [item.section for item in second.see] == ['4446', '4447']
    assert third.succession is Succession.OMITTED and not third.targets


def test_a_range_of_subdivisions_covers_each():
    assert Provision('CIV', '1111', '(a)-(e)').tops() == ('a', 'b', 'c', 'd', 'e')
    assert Provision('CIV', '1111', '(e)(1)-(2)').tops() == ('e',)


def test_a_comment_sentence_reads_into_how_the_provision_continues():
    comment = (
        'Subdivision (a) of Section 9001 continues former Section 1111(b) without change. '
        'Subdivision (b) continues the substance of former Section 1112. '
        'Subdivision (c) is new.'
    )
    found = succession.read_comment('CIV', '9001', '1', comment, 'test', Report.RECOMMENDATION_2011)
    readings = [(row.former and row.former.label(), row.targets[0].label(), row.succession) for row in found.rows]
    assert readings == [
        ('1111(b)', '9001(a)', Succession.CONTINUED_WITHOUT_CHANGE),
        ('1112', '9001(b)', Succession.CONTINUED_WITHOUT_SUBSTANTIVE_CHANGE),
        (None, '9001(c)', Succession.NEW),
    ]


def test_a_listed_substantive_change_makes_the_continuation_changed():
    comment = (
        'Section 9002 continues former Section 1113 without change, except as indicated below. '
        'The following substantive change is made: one. '
        'The following nonsubstantive change is made: two.'
    )
    found = succession.read_comment('CIV', '9002', '1', comment, 'test', Report.RECOMMENDATION_2011)
    assert found.rows[0].succession is Succession.CONTINUED_WITH_CHANGES


def test_a_section_outside_any_recodification_is_a_miss():
    missed = succession.successors('CIV', '1940')
    assert missed['found'] is False and missed['reason'] == 'not_recodified'


# --- The shelf and the Commission's documents, when present.

_SHELF = bool(history.code_editions('CIV'))
_TABLE = succession.text_of(Report.AB805_DISPOSITION) is not None


@pytest.mark.skipif(not _SHELF, reason='shelf with code editions missing')
def test_a_former_section_is_present_then_repealed():
    found = history.section_history('CIV', '1363')
    assert found['found'] and not found['current']
    repealed = [row for row in found['steps'] if row['change'] == 'repealed']
    assert repealed and repealed[0]['before'] == found['last']
    if _TABLE:
        assert repealed[0]['statute'].startswith('Stats. 2012, Ch. 180')


@pytest.mark.skipif(not _SHELF, reason='shelf with code editions missing')
def test_a_current_section_names_its_latest_act_in_each_edition():
    found = history.section_history('CIV', '5855')
    assert found['found'] and found['current']
    added = [row for row in found['steps'] if row['change'] == 'added']
    assert added and added[0]['statute'].startswith('Stats. 2012, Ch. 180')
    for row in found['steps']:
        if row['change'] == 'amended':
            assert row['statute'] and row['summary']


@pytest.mark.skipif(not _SHELF, reason='shelf with code editions missing')
def test_the_change_list_runs_oldest_first():
    found = history.changes('CIV', [('5850', '5875')], since=2011)
    assert found['found']
    befores = [row['before'] for row in found['changes']]
    assert befores == sorted(befores)


@pytest.mark.skipif(not (_SHELF and _TABLE), reason='shelf or Commission table missing')
def test_the_table_places_a_former_subdivision():
    found = succession.successors('CIV', '1363', '(g)', candidates=False)
    tables = [row for row in found['rows'] if row['source'] == 'disposition_table'
              and row['act'] == 'davis-stirling']
    assert tables and all(row['former']['subdivision'] == 'g' for row in tables)
    reverse = succession.predecessors('CIV', tables[0]['targets'][0]['section'], candidates=False)
    assert any(row['former'] and row['former']['section'] == '1363' for row in reverse['rows'])


@pytest.mark.skipif(not (_SHELF and _TABLE), reason='shelf or Commission table missing')
def test_coverage_counts_every_former_section_once():
    found = succession.coverage('davis-stirling', candidates=False)
    sections = found['sections']
    assert sections['total'] == sections['by_table'] + sections['left_out'] + sections['unplaced']
    assert sections['by_table'] > 0
