---
name: index-structure
description: >-
  Develop lawlibrary parsers against sampled California sections. Use when
  indexing a code, annotating citations, splitting subdivisions such as (a)
  (b) (1) or IV., tracing related statutes to a depth, drawing a mermaid
  diagram beside the plaintext,   or sampling cuts, needles, refs, entities,
  antecedents, case, dollar amounts, periods, dates, quantity phrases,
  citations, series joins, clauses, signals, sessions, history actions, headings, or sentence parts.
---

# Index structure

California is the citation system. One cycle samples every surface, then extends the helper for that surface. Do not invent a quotation. A miss stays a miss.

## Cycle

1. Draw one section for each surface in Sample. Start with `sample.sample` or `query.section` for a cut. When that text has no hit for the next surface, open a citation from `Indexer.annotations`. For a note, draw a common target and a rare target, as Frequency describes. For a quantity, also read `Duration.shape`, `Monetary.shape`, and `Absolute.shape`. `shapes` counts that phrase. The stored target keeps the number.
2. `structure.split_nodes` builds the hierarchy. `(a)` and `(b)` are siblings. `(1)` sits under the open letter. `IV.` is a roman heading.
3. `structure.find_links` records `Section 7280 of the Revenue and Taxation Code` as code `RTC` section `7280`, `subdivision (b)` as a label, and `this chapter` as internal.
4. `structure.related(code, number, depth)` follows statute links. Depth 0 is the section alone. A positive depth is that many hops. `None` or a negative depth follows until a section is repeated. The default is 1. The same section is not visited twice, so the chart stays a DAG.
5. Put the Markdown page beside `text`. `Citation(code).section(number).hops(depth).md` is that page. `refs` is the node and `follow()` opens the next statute. A larger depth goes further. `Diagram.codes()`, `Diagram.vesting()`, and `Diagram.enactments()` are the stored graphs.
6. Read [parser-pitfalls.md](../../../docs/lexical/parser-pitfalls.md) first. `structure.review(code, number, depth)` compares citation-shaped phrases in the retrieved text with the links `find_links` recorded. A short title stopped at the first word `Code`. An unresolved book is not one of the codes. An unlinked phrase was not recorded. Pass a `Code` member. The section number stays the printed text. A random draw is `sample.sample(book, n=20, seed=None)` and a review depth of 2.
7. Every gap is fixed in that same cycle. Write the row before changing the parser: the citation on the gap, the kind, and what the parser did. Then change `structure.py`. Then move the row to Recorded and state what to avoid. Do not leave a new gap under Open.
8. Add a case that parses that citation and looks the section up. A citation gap goes in `tests/test_structure.py`. A gap on another surface goes in that surface's test. Lock the common target and one rare target from Frequency. For a quantity, also lock `shape()`: the common phrase, and one rare period phrase. An amount stays `monetary`. A date stays `absolute`. Do not paste the sentence into the test. An unknown book stays unresolved. Record that, and do not assign it to the open book.
9. When the cycle changes a stored annotation, reindex with `Indexer.index_stored_needles(workers=n)`. That rewrites needle, edge, and annotation rows from the text already in the index. Case, cut, session, a folded short form, and a citation's `cite` and `join` are stored by that pass. `workers` above 1 parse sections in other processes. Term rows and annotation rows are separate jobs. The SQLite connection only inserts them and is not shared across threads. Do not call `index_pubinfos` or `reset`. Do not wipe `data/idx`. Until that pass finishes, sample the new note with `annotate` on the looked-up text.

## Sample

One cycle covers every surface. Open the section with `query.section` or `Citation.text`. Do not paste the sentence into the skill or the test. A miss on a surface stays a miss for that section. Draw the next citation for that surface. Do not skip the surface.

| Surface | Draw | Read |
| --- | --- | --- |
| Cuts | `(a)`, `(1)`, `subdivision` | `split_nodes`, `muster`, `breakdown(code)`, `Note.CUT` |
| Needles | the open book | `consider(code)`, `occurrences(text)`, `Indexer.needles(code)` |
| Refs | a section that cites another statute | `Citation.section(n).hops(depth).refs`, `links()`, `follow()`, `sessions`, `articles` |
| Entities | an office or a short form in the text | `compose`, `find_mentions`, `abbreviations`, `seats` |
| Antecedents | `note='antecedent'` | `find_durations` |
| Uppercase | `note='case'`, `target='uppercase'` | `Note.CASE`; `capitals` with `reading` `name` |
| Title case | `note='case'`, `target='title'` | `Note.CASE`; a run of Capitalized words |
| Dollar amount | `note='amount'` | `Monetary.parse`; the target is integer dollars. `shape` is `monetary` |
| Period | `note='period'` | `Duration.parse`, `find_durations`. `shape` replaces the count with `duration` |
| Date | `note='date'` | `Absolute.parse`; month, day, and year. `shape` is `absolute` |
| Quantity phrase | the same three spans | `shapes(note, rows)`. A common phrase and a rare phrase, from Frequency |
| Citations | a section sign or `Section N of the ... Code` | `find_citations`; `Note.CITATION` |
| Series | numbers joined by `,`, `;`, `and`, `or`, or `and/or` | Iterate the point. `Join.CONJUNCTION`, `Join.DISJUNCTION`, `Join.BOTH`. Each number is its own citation. The stored row keeps `cite` and `join` |
| Clauses | a customary span in the text | `find_clauses` |
| Signals | shall, may, means, includes | `find_signals` |
| Relations | an office placed by an enactment | `find_relations`, `find_enactments`, `grants` |
| Session | `note='session'`, and the history line | `Action`, then year, then chapter. Not a code chapter |
| Headings | the heading path | `heading_notes`. `PART` is a cut of the division. `headings` counts that surface. `marks` counts the body |
| Sentences | the same text | `Citation.sentences`; a part is rule, condition, exception, or limit |
| Graphs | the citation, then the stored graphs | `refs.md`, `Diagram.codes()`, `Diagram.vesting()`, `Diagram.enactments()` |

`Indexer.annotations(note, code, target)` returns the stored citations. Those rows are written when the section is indexed. Step 9 rewrites them from the text already stored. Stored `case`, `cut`, and `session` rows are absent until that pass. Until then, run `annotate` on the looked-up text and keep every `Note.CASE`. Do not skip uppercase or title case. A dollar amount, a period, and a date are three draws. Each draw has a target and a phrase. `Monetary.parse`, `Duration.parse`, and `Absolute.parse` are those readers. `shape` is the phrase. Do not add `find_dollar_amount`, `find_quantity`, or `find_date`. Do not call `rank` or `common` on the live index from a test.

## Frequency

A common mark is in every code. A rare mark is in one. Sample both. `Indexer.targets(note)` lists the stored targets by count. `top` is the common end. `bottom` is the rare end. A quantity phrase is not stored. Group the period rows with `Duration.shape`, then take `top` and `bottom` of that list. An amount phrase and a date phrase have one member each. A short form target is folded, so `ET SEQ.` counts as `et seq.` The annotation table stores the code only. Chapter, division, article, state, and federal are not in that table, so a miss there stays a miss.

| Mark | Common | Rare | Absent |
| --- | --- | --- | --- |
| Needle | `shall`, `section`, `may` | `do ordain as follows`, `subitem` | a noun title has no stored rows |
| Amount | `1000`, `10000` | a sum in one code | none of the 30 codes |
| Period | `1 year`, `within 30 day` | `39 month`, `1 business day` | none of the 30 codes |
| Quantity phrase | `duration year` (30 codes), `within duration day` (29) | `from duration court day`, `until duration working day` | an amount has no rare phrase; every sum is `monetary`. A date has none; every calendar day is `absolute` |
| Short form | `et seq.`, `as amended` | `ET SEQ.`, `As amended` | Evidence Code |
| Named act | `Administrative Procedure Act` | — | Commercial, Constitution, Elections, Harbors and Navigation, Public Contract, Probate, Streets and Highways, Unemployment Insurance |
| Antecedent | `the hearing` | `death` | none of the 30 codes |
| Case, cut, session | — | — | every code, until step 9 |
| History action | `added`, `amended` | `repealed`, `repealed conditionally` | stored targets, until step 9. Read the history line with `annotate` |
| Series join | `conjunction` (23859, 30 codes), `disjunction` (17030, 30 codes) | `both` (24, 1 code) | a series whose `join` is empty (1433, 27 codes). `cite` `section` is 117077 and `range` is 1959, both in 30 codes |

A target in every code is a needle or a quantity, not a new word class. `useful_needles` makes that split. A quantity phrase is that split with the number removed. `duration year` is common because the count varies and the phrase does not. `monetary` and `absolute` have no rare end. Sample a rare period phrase from `bottom`. The count does not add the phrase to `forms`. A phrase that is useful in the code scope can still be rare in one chapter. `document` records the members. A long code has more rows than a short one. The count is not a rate.

## Related

These sit beside the required draws. Search them on the section Sample already opened, or on the catalog that names them. A miss stays a miss. Do not add a finder whose name is not already a helper.

| Surface | Search | Read |
| --- | --- | --- |
| Cross-reference | `note='cross_reference'` | `this chapter`, `commencing with Section` |
| Named act | `note='named_act'` | a statute cited by its title |
| Short form | `note='short_form'` | `et seq.`, `supra`, `id.`, `as amended` |
| Citation span | the same text | `find_citations`; `Cite.SECTION`, `Cite.RANGE`, `Cite.SERIES` |
| Series join | the same text | Iterate the series. `Join.CONJUNCTION` is `and`. `Join.DISJUNCTION` is `or`. `Join.BOTH` is `and/or`. Count stored `cite` and `join` |
| Place named in the text | the same text | `find_mentions`; `Kind.STATE`, `COUNTY`, `CITY`, `COURT`, `AGENCY` |
| Duty of an office | the same text | `find_relations`; `Relation.DUTY`, `POWER`, `APPOINTMENT`, `SUPERVISION` |
| One clause | the same text | `find_clause(text, clause)` for one `Clause` member |
| One canon | the same text | `find_signals(text, canon)` for one `Canon` member |
| Citation gap | `review` on the walk | `Gap.SHORT_TITLE`, `UNRESOLVED`, `UNLINKED` |
| Local short form | the same text | `abbreviations`; a parenthesis after the first full name |
| Terms | the open book | `Scope.CODE(token).rank`, `.common`, `.terms()` |
| Outline | a heading span | `outline_law`, `tree_law` |
| Session law | a year and a chapter | `session_law`, `act_law`. A history credit is `Action` then `Stats.` The chapter row on the section includes `action` |
| Heading count | the heading text | `Surface.HEADING`, `Scope.CODE(token).headings(note, rows)`. A body row is `marks` |
| Other instrument | `sample(book, kind=...)` | `Instrument.REGULATION`, `RULE`, `MANUAL`, `MEASURE` |
| Office or court | the catalog, not the sentence | `list_offices`, `list_courts` |
| Pinned reading | the citation | `list_pins`, `pin_section` |
| Style rule | a posted guide | `search_style_manual` |

## Tools

`related_law` returns the plaintext, the subdivision labels, the links, the mermaid chart, and `page`. `diagram_law` returns a stored graph as that same page. `review_law` returns the gaps from the same walk. `annotations_law(note, code, target)` selects stored annotations. A citation row includes `cite` (`section`, `range`, or `series`) and `join` (`conjunction`, `disjunction`, or `both`). For case, `target` is `uppercase` or `title`. For a session credit, `target` is the action, the year, and the chapter, such as `added 2011 383`. A chapter cited with no history verb stays the year and the chapter. `get_section` returns `chapters`, and each row has `action` when the history names one. `search_style_manual` with guide `indigo` checks a posted rule such as `R17` when the form is in doubt. Lesser manuals are not fetched.

## Fan out

Read each surface on the section that Sample drew for it. Each area has its own helper. Do not fold them into `find_links`.

### Series

A series is one citation that iterates one section at a time. `and` is `Join.CONJUNCTION`. `or` is `Join.DISJUNCTION`. `and/or` is `Join.BOTH`, and both readings stay. A comma or a semicolon with no coordinating word is still a series, and `join` is empty. Each number is its own `Note.CITATION` with `cite` `series`. The stored row keeps `cite` and `join`. Count those columns on `note='citation'`. Sample a conjunction and a disjunction. Do not collapse the items back into one span.

### Entities

`analysis.compose` applies each `needles.Noun` rule. `Phrase.reading` is `office` or `unit`. `mentions.find_mentions` classifies by frame. An unknown name stays a mention. `hierarchy.seats` places a child under a parent when the enactment says so. Empty seats is a miss. Extend the matching `Noun` (`forms`, `rules`, `examples`). Do not add a JSON roster.

### Antecedents and modifiers

A relative period keeps its relation on `Duration.lead` and `Duration.trail` (`from`, `prior to`, `within`, `after`). `find_durations` stores the forward noun phrase on `Duration.antecedent`. `such`, `that`, and `thereof` point backward. `from` and `prior to` point forward. A trailing modifier on a list is `Canon.LAST_ANTECEDENT` and `Canon.SERIES_QUALIFIER`. When both fire, `ambiguities` keeps both readings. Do not pick a winner.

### Proper nouns

`annotate` records `Note.CASE`. The target `uppercase` is an all-capital word of three or more letters in a mixed sentence. The target `title` is a run of Capitalized words, optionally joined by of, the, and, for, or &. Sample both. `annotations_law('case', target='uppercase')` and `annotations_law('case', target='title')` are the stored draws. A whole paragraph in capitals is emphasis and is not a case note. Call `analysis.capitals` on looked-up text and keep a hit only when `reading` is `name`. Leave `emphasis` unmarked as a party. Until a looked-up section prints an ALL CAPS party, do not paste a specimen. An acronym may also match `name`.

### Quantities and qualifiers

Sample a dollar amount, a period, and a date as three sections. On each section read the target and the phrase. `Monetary.parse` reads a spelled sum plus `($100,000)` and a bare `$` figure. The target is integer dollars. `Monetary.shape` is `monetary` for every sum, so an amount has a common target and a rare target, and one phrase. `Note.AMOUNT` stores the target. `Duration.parse` and `find_durations` read a count of days, months, or years, including the qualifier `calendar`, `legislative`, `business`, `working`, or `court`. `Duration.shape` leaves the lead, the qualifier, the unit, and the trail, and puts `duration` where the count was. `within 30 days` and `within 95 days` are `within duration day`. `1 business day after` is `duration business day after`. `Note.PERIOD` stores the target, including the count. Draw the common phrase `duration year` and a rare phrase such as `from duration court day` or `until duration working day`. `Absolute.parse` reads a month, a day, and a year. `Absolute.shape` is `absolute` for every calendar day, so a date has a common target and a rare target, and one phrase. `Note.DATE` stores the target. A year alone is not an absolute date. A count of days is not a date. A citation number is not a quantity. `shapes(note, rows)` counts the phrase. `marks` still counts the target. `find_citations`, `find_clauses`, and `find_signals` classify the other spans on that same text.
