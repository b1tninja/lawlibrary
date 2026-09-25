# Terms

Official words, and the class that holds each one. An agent starts here, then opens the source file for the sentence. The words live in `needles.py`. Ask `consider(code, shelf)` for the classes that apply to the open book. A subclass replaces its base in that book. It does not apply to every law.

The sentences those bodies published are in [docs/lexical/sources/terms.md](docs/lexical/sources/terms.md). The publications themselves are indexed in [docs/lexical/drafting.md](docs/lexical/drafting.md).

## How to use a term

1. Find the class in the table below.
2. Call `consider(code)` or `consider(shelf='joint-rules')`. If a subclass is in the result, use that reading.
3. Search with `pattern` or `cuts`. Do not copy the word list into a hunter or a test.
4. Quote a sentence only from the source file named here, or from `query.section`.

`PublicUtilities().words()` is the Public Utilities Code. `JointRules().words()` is the Joint Rules. Any other open book gets the general classes.

## Word classes

| Class | Words | Applies | Official source |
| --- | --- | --- | --- |
| `Section` | section | Every law | [usc-1-104.md](docs/lexical/sources/usc-1-104.md), [holc-guide.md](docs/lexical/sources/holc-guide.md) part III |
| `CodeSection` | section, subdivision | The codes that define those words for themselves | BPC 15, CORP 10, EVID 7, FGC 73, FIN 9, GOV 10, HNC 10, HSC 10, INS 10, PUC 10, RTC 10, UIC 9, VEH 11, WAT 10, WIC 10 |
| `PublicUtilitiesSection` | section, subdivision | Public Utilities Code only | [puc-10.md](docs/lexical/sources/puc-10.md) |
| `Article` | article | Every law | [holc-guide.md](docs/lexical/sources/holc-guide.md); a constitution article is article plus section |
| `Bill` | bill | Every law except the Joint Rules | A measure introduced in a house |
| `JointBill` | bill | Joint Rules only (`shelf='joint-rules'`) | [joint-rules-2019.md](docs/lexical/sources/joint-rules-2019.md) rule 4 |
| `Act` | act | Every law | [holc-guide.md](docs/lexical/sources/holc-guide.md): inside the quotes, “this Act” is the statute being amended |
| `Part` | part | Every law | `this part` |
| `Chapter` | chapter | Every law | `this chapter` |
| `Division` | division | Every law | `this division` |
| `Title` | title | Every law | `this title` |
| `Subtitle` | subtitle | Every law | [house-manual-2022.md](docs/lexical/sources/house-manual-2022.md) |
| `Subchapter` | subchapter | Every law | [holc-guide.md](docs/lexical/sources/holc-guide.md) part III |
| `Subpart` | subpart | Every law | [holc-guide.md](docs/lexical/sources/holc-guide.md) part III |
| `CodeWord` | code | Every law | `this code` |
| `Paragraph` | paragraph | Every law | `this paragraph` |
| `Constitution` | constitution | Every law | `this constitution` |
| `Modal` | shall, may, may not | Every law | [holc-guide.md](docs/lexical/sources/holc-guide.md): shall requires, may permits, may not denies |
| `Vesting` | vested with, vested in, succeed to | Every law | Government Code section 12802. A vested property right is not this phrase |
| `Enactment` | do enact as follows, do ordain as follows, does ordain as follows | Every law | Government Code section 9501.5; Elections Code section 9224 for an ordinance |
| `Definition` | means, includes | Every law | [holc-guide.md](docs/lexical/sources/holc-guide.md): means is exclusive, includes is not |

`this` plus one of those words is an internal reference. `pattern(internal=True)` builds that expression. `annotate` and `find_links` use it.

## Cuts under a section

`Section.cuts` is the label vocabulary. `cuts()` returns it. A label is the word plus a mark, as in `subdivision (b)` or `subsection (d) of Section 12867`.

| Mark | House name | California name |
| --- | --- | --- |
| `(a)` | subsection | subdivision |
| `(1)` | paragraph | paragraph |
| `(A)` | subparagraph | subparagraph |
| `(i)` | clause | clause |
| `(I)` | subclause | |
| `(aa)` | item | |
| `(AA)` | subitem | |

The House order is in [house-manual-2022.md](docs/lexical/sources/house-manual-2022.md) page 20. California’s word for `(a)` is in [puc-10.md](docs/lexical/sources/puc-10.md). A further cut must nest inside the one before it. `muster` reports a break. It does not decide that the text is void.

Each label is a `Cut`. A breakdown is an instance of a subclass of `Breakdown`, read with `members`. It is the units inside a section. `House` starts at subsection. `California` starts at subdivision and does not include subsection. `Insurance` subclasses `California` and adds subsection, from Insurance Code section 10. `General` is every cut. `breakdown(code)` returns that instance. `cuts()` still returns every word, so a federal subsection in a California code still parses. `annotate` records each cut as `Note.CUT`. The target is the word. A definition target ends in `means`. The ladder above a section is the organization, held by `Outline`. A heading is only the caption. A designation is a mark assigned to a provision, such as its section number.

## Readings that belong to one book

| Words | Book | Class | Source |
| --- | --- | --- | --- |
| section, subdivision | Public Utilities Code | `PublicUtilitiesSection` | [puc-10.md](docs/lexical/sources/puc-10.md) |
| bill | Joint Rules | `JointBill` | [joint-rules-2019.md](docs/lexical/sources/joint-rules-2019.md) rule 4 |
| heading | Welfare and Institutions Code | not a class yet | [wic-6.md](docs/lexical/sources/wic-6.md). Headings shall not govern the text. |

A heading is recorded as a source. It is not yet a `Word` subclass, so `consider` will not return it.

## Uses from a sample of 100 hits

A random draw of 100 needle hits in the California index was read in four parts: [1–25](e62b59ff-72a0-4aa7-9d4b-4ae424a01d76), [26–50](c393113c-1879-4daa-86fe-f0a23a8cac78), [51–75](44a3cd53-d7ea-4e9e-99b9-04a8705560fb), and [76–100](9f2bba3a-e252-4d2c-99e3-0b6c9b10f3bb). Ordinary `shall` and `may` stay on `Modal`. These uses changed the reading often enough to mark:

| Use | Mark | Example from the index |
| --- | --- | --- |
| `as the case may be` | not `Canon.PERMISSIVE` | Public Utilities Code section 7578 |
| `this article shall not apply` | `Clause.APPLICATION` | Streets and Highways Code section 31200 |
| `"Term" means` without "as used in this" | `Clause.DEFINITIONS` | Unemployment Insurance Code section 13007 |
| `has the same meaning as` | `Clause.DEFINITIONS` | the same definition frame |
| `shall constitute`, `shall be void` | `Clause.EFFECT` | Public Utilities Code section 29153 |
| `No person shall`, `No claim shall` | `Clause.PROHIBITION` | Water Code section 13750.5 |
| `does not affect the rights` | `Clause.SAVINGS` | already the savings frame, now with "the rights" |
| county auditor, board of supervisors, Secretary of State, and the other titled offices in `mentions._OFFICES` | `Kind.AGENCY` | Water Code section 70237 |

Bare `the department` and `the commission` name whoever the open section already named. They are not a new entity. Bare `act`, `part`, and `title` are often ordinary English. The internal mark is `this act`, `this part`, and `this title`.

## Clauses the drafting manuals name

The House manual and the HOLC guide name these jobs. The ones already marked stay on `Clause`. The sample confirmed the rest in the California index. An urgency clause was not in the sections that search opened, so it is not a mark.

| Clause | Words | Source |
| --- | --- | --- |
| `Clause.APPROPRIATION` | is hereby appropriated; authorized to be appropriated | House manual section 327; Insurance Code section 12699.525 |
| `Clause.CONSTRUCTION` | shall be liberally construed; the singular number includes the plural; rules of construction | HOLC on title 1; Government Code section 13; Food and Agricultural Code section 78428 |
| `Clause.NONSEVERABILITY` | if a portion is void, the entire chapter becomes inoperative | House manual section 328 describes the opposite, severability. Government Code section 77400 is the California form that takes the whole chapter down |
| `Clause.SHORT_TITLE` | may be cited as, as well as known as | House manual section 323; Welfare and Institutions Code section 11200 |
| `Clause.SEVERABILITY` | if any provision of this code is invalid | Education Code section 6. The earlier pattern stopped at chapter and missed code |

## Names that collide

The same English word is two records. The class in the first column is the one that holds the word. The other reading is a different class.

| Class | Word | The other reading |
| --- | --- | --- |
| `Session` | chapter | `Chapter` is `this chapter` inside a code. Chapter 142 of the Statutes of 2023 is `Session.year(2023).chapter(142)`. |
| `Action` | added, amended, enacted, repealed, repealed and added, repealed conditionally | The history verb in front of `Stats.` The session target stays year then chapter. The annotation target is the action, then that year and chapter. |
| `Session` | section | A code section is `Citation` and `Section`. Section 4 of that chapter is `Session.section(4)`, the enrolled bill's own section, stored as `act`. |
| `Article` | article | A constitution article identifies the section (`ConstitutionOutline`). A code article is a heading in `Outline.order` and is left out of the section citation. |
| `Session` | session, year | The year is the calendar year the Secretary of State assigned the chapter. The Whoosh `SESSION` field is that same year on a stored section. It is not the two-year legislative session. |
| `Draw` | choose | `choose()` returns the sampled sections. A graph is a separate drawing. `citations()` is the list of those sections and can be sliced. |
| `Section` | subdivision, subsection | California `(a)` is a subdivision in a code that defines the word (`CodeSection`). The House manual calls `(a)` a subsection. Insurance Code section 10 names both, and the other cuts stay so a federal subsection still parses. |
| `Place` | page, line | `page(12).line(5)` is a bill sheet. A parenthetical on a section number is a cut, such as subdivision `(a)`, not a page. |
| `Lexicon` | rank, common | `rank` is the distinctive terms. `common` is the terms shared across the scope. Neither is `structure` rank of a parenthetical mark. |
| `Note` | case | `as the case may be` is not `Canon.PERMISSIVE` and is not `Note.CASE`. `Note.CASE` is `uppercase` or `title`. |
| `Ends` | top, bottom | `top` is the start of an ordered list. `bottom` is the end. `head` is a heading, and the first word of `this section`. `tail` is the words in front of a title. |
| `Ends` | where, unique | `where('useful')` and `where('expression')` keep a flag. `without` drops it. `unique` keeps the first row for each term or phrase. `descending` and `ascending` sort a count. `order` is `Outline.order`. `rank` is the distinctive term list. |

## Surfaces on a section

A surface is a closed set. The member is the word a file may store. `Indexer.annotations(note, code, target)` selects a stored `Note`. `annotate` writes the note on looked-up text. A dollar amount, a period, and a date stay three notes. `Monetary.parse`, `Duration.parse`, and `Absolute.parse` are those readers.

| Member | What it marks | Helper |
| --- | --- | --- |
| `Note.CITATION` | a section sign or `Section N of the ... Code` | `find_citations` |
| `Note.CROSS_REFERENCE` | `this chapter`, `commencing with Section` | `annotate` |
| `Note.NAMED_ACT` | a statute cited by its title | `annotate` |
| `Note.SHORT_FORM` | `et seq.`, `supra`, `id.`, `as amended` | `annotate` |
| `Note.AMOUNT` | a dollar amount; the target is integer dollars | `Monetary.parse` |
| `Note.PERIOD` | a count of days, months, or years | `Duration.parse`, `find_durations` |
| `Note.DATE` | a month, a day, and a year | `Absolute.parse` |
| `Note.SESSION` | a year, then a chapter of the statutes | `annotate` |
| `Note.CUT` | a cut word; a definition target ends in `means` | `annotate`, `breakdown(code)` |
| `Note.CASE` | `uppercase` or `title` | `capitals`; keep `reading` `name` |
| `Cite.SECTION`, `Cite.RANGE`, `Cite.SERIES` | how many sections the sign introduces | `find_citations` |
| `Join.CONJUNCTION`, `Join.DISJUNCTION`, `Join.BOTH` | `and`, `or`, or `and/or` on a series. Iterating the series yields one section | `find_citations` |
| `Kind.STATE`, `COUNTY`, `CITY`, `COURT`, `AGENCY` | what a name in the text is | `find_mentions` |
| `Relation.DUTY`, `POWER`, `APPOINTMENT`, `SUPERVISION` | how a sentence ties an office to a job | `find_relations` |
| `Quantity.MONETARY`, `DURATION`, `ABSOLUTE` | the measured element | `Monetary`, `Duration`, `Absolute` |
| `Convention.USD`, `GROUPED`, `DECIMAL`, `MONTH_DAY_YEAR`, `ISO_8601`, `NUMERIC_MDY`, `YEAR`, `MONTH`, `DAY` | how the value is printed. The target stays the number or `YYYY-MM-DD` | `convention()`, `Parser.formats` |
| `Gap.SHORT_TITLE`, `UNRESOLVED`, `UNLINKED` | a citation shape the links did not record | `review` |
| `Instrument.STATUTE`, `MEASURE`, `REGULATION`, `RULE`, `MANUAL` | what an edition contains | `sample(book, kind=...)` |

`abbreviations` records a short form introduced in parentheses after the first full name. `find_clause` reads one `Clause`. `find_signals` reads one `Canon`. `list_offices` and `list_courts` are the catalogs. `list_pins` is a stored reading. `outline_law` and `tree_law` are the heading ladder. `session_law` and `act_law` are a year and a chapter.

## Where the helpers are

| Job | Helper |
| --- | --- |
| Classes for this book | `needles.consider` |
| Surface words | `needles.forms` |
| One expression for those words | `needles.pattern` |
| Label words | `needles.cuts` |
| shall, may, means, includes | `canons.find_signals`, using `Modal` and `Definition` |
| this section, this article, and the other internal words | `citations.annotate`, `structure.find_links` |
| Outline of one section | `structure.split_nodes`, `muster.muster` |
| Distinctive words in a code, chapter, division, state, or federal text | `Scope.CODE(token).rank` |
| Shared words in that same scope | `Scope.CODE(token).common` |
| The term set for that scope | `Scope.CODE(token).terms()`. Calling the lexicon returns that frozenset. `terms('common')` is the shared set |
| Identified terms for one note | `Scope.CODE(token).marks(note, rows)` returns `Noted` for the body. `headings(note, rows)` is the same note on headings. `Surface` is `heading` or `body`. A heading row does not add to the body count. The same call works for `CHAPTER`, `DIVISION`, `ARTICLE`, `STATE`, and `FEDERAL`. The first field is that member. `af` is the count in the member on that surface. A case term is the printed word. An amount term is the target, digits included |
| A quantity counted without its number | `Scope.CODE(token).shapes(note, rows)`. The stored target keeps the count. `within 30 days` and `within 95 days` share `within duration day`. An amount is `monetary`. A date is `absolute`. A citation number stays on the mark |
| Words around a quantity | `frames(text)` and `Scope.CODE(token).frames(rows)`. Three words before the span and two after, in the same sentence. The figure is the classifier, so `not more than $1,000` and `not more than $10,000` are `not more than monetary` |
| A phrase grown from both sides | `Scope.CODE(token).extend(rows, anchor)`. `pairs` keeps one word on each side. `extend` walks outward. A neighbor stays when more than half the members that contain the anchor have that same word on that side. Six words is the furthest on one side. `measure_tokens` puts the quantity shape in the word list |
| A phrase hunted from the index | `Indexer.hunt(anchor)` phrase-searches `LEGAL_TEXT`. `Scope.CODE(token).hunt(rows, anchor)` counts every overlapping successive pair in one pass, then chains them. A neighbor is kept when more than half the current members share that pair, and the scope becomes those members. The walk stops when one member is left. `distance` is how many words were added. Do not call the live index from a test |
| Annotation frequency by cut | `Scope.CHAPTER('FGC 1').cuts(rows, note)`, and the same for the other scopes. A cut note's target is the cut. A fifth field assigns any other note to a cut. A row with no cut is left out |
| Which identified terms are needles | `useful_needles(weights, n)`. A form, or `this` plus a form, is a needle. An amount, a period, or a date is a quantity. A shared unmatched word is a candidate. A rarer word stays a weight |
| Needle frequency | `Scope.CODE(token).needle_count(rows)` returns `Needle`. `nf` counts a form, apart from term frequency and annotation frequency. `this` plus a form counts as the form. Any other word is left out |
| Words seen together | `Scope.CODE(token).pairs(rows)` returns `Pair`. `pf` counts two adjacent words in that order. `expression` is true when the phrase is already a form |
| Every successive pair | `Scope.CODE(token).successive(rows)`. One pass over overlapping pairs. `pf` is the count. `df` is how many members contain the pair. The rank limit does not apply. An annotated value is also counted as a placeholder, separately from the printed pair: `{SECTION}`, `{CODE}`, `{YEAR}`, `{AMOUNT}`, `{QUANTITY}`, or the quantity type such as `duration` |
| Where a phrase is useful | `Scope.CODE(token).document(rows)` returns `Phrase` for each scope. `members` are the keys that contain it. `useful` means at least half of those members. A useful phrase that is not an expression is a candidate. The count does not add it to `forms`. `top`, `bottom`, `where`, `without`, `unique`, `descending`, and `ascending` close over that list |
| A few sections from one book | `Draw(code).take(n).seed(seed).choose` |
| Needle hits stored when a section is indexed | `Indexer.needles`. A class is stored only when `consider` says it applies to that code or shelf |
| Stored annotations | `Indexer.annotations(note, code, target)`. `case` is `uppercase` or `title`. `amount`, `period`, and `date` are separate notes. `Indexer.targets(note)` lists targets by count. `top` is common. `bottom` is rare. A short form target is folded, so `ET SEQ.` counts as `et seq.` |
| A name in the text | `mentions.find_mentions`. `Kind` is state, county, city, court, or agency |
| A short form introduced beside the name | `mentions.abbreviations` |
| How an office is tied to a duty | `mentions.find_relations`. `Relation` includes duty, power, appointment, and supervision |
| An enactment that places an office | `mentions.find_enactments`, `vesting.grants`, `hierarchy.seats` |
| One customary clause | `lexical.find_clause` |
| One canon | `canons.find_signals(text, canon)` |
| A citation the links missed | `structure.review`. `Gap` is short title, unresolved, or unlinked |
| A heading span, or the URL tree | `query.outline`, `query.law_tree` |
| A session law | `query.session_law`, `query.act` |
| Another instrument | `sample.sample(book, kind=...)`. `Instrument` is statute, measure, regulation, rule, or manual |
| Offices and courts | `agency.agencies`, `court.courts`. `entities.list_entities` is a country, a state, a county, or a city |
| A posted style rule | `companions.search_manual` |
| A pinned reading | `analysis.pins`, `analysis.pin` |
| A stored graph as a Markdown page | `Diagram.codes().page()`, `Diagram.vesting().code(code).page()`, `Diagram.enactments().code(code).page()`, `Diagram.around(citation).page()`. `chart()` is the flowchart alone |
| One section and the statutes it cites | `Citation(code).section(n).hops(depth).refs`. `md` and `chart` share one walk. `follow()` opens the next statute. `sessions` is the year and chapter. `articles` is the article and section. `links()` is the pointer list |
| The stored plain text of a citation | `Citation(code).section(n).text`. `words()` is that text split on whitespace. `subdivisions` are the labels. On a needle class, `words()` is the word classes |
| The WSGI callable | `application:application`. GET `/` is the code index inside `noscript`, so a legacy browser reaches the home page. `/tree/{url}`, `/section/{code}/{number}`, `/annotations`, `/closure`, and `/view` stay linkable. A miss is found false. React mounts on `#root` |
| A closure the client opened | `GET /closure`. `code` is the book. `division`, `title`, `part`, `chapter`, `article`, `section`, and `subdivision` remember the unit above. `session` is the year. `hops` is the walk, and `all` follows until a section repeats. `only` is a comma-separated book list. `same=1` stays in the open book. `q` searches inside the place. `use` is `read`, `find`, or `refs`. A missing use follows the filters that were sent |
| A hovered term | `GET /term`. `q` is the word or phrase. `note` and `target` select a stored annotation. The reply is `frequency` (`pf`, `df`, and `indexed` for one Whoosh token), `neighbors` (the pairs beside the term in those hits), and `occurrences` (a citation, a snippet, and an href). `glance(term, rows)` is that count on rows already in hand |
| Full text | `GET /search`. `q` is words, a phrase, or a citation. `code`, `start`, `end`, `session`, and `limit` are filters on `query.search`. A span drops hits outside it. The reply is `hits` |
| The reference set | `GET /mirror` and `GET /mirror/{url}`. One HTML file per node. A directory lists the next headings. A section file is the citation, the heading path, the stored text, and the history line. `wget --mirror --no-parent` follows the links |
| A format hint | `Hint`. A suffix on the section path: `.html`, `.txt`, `.xml`, `.pdf`, or `.md`. `1714.1.txt` is still section 1714.1. `.md` is `text/markdown`: the citation, the headings, the text, the history, the reference links, and a fenced flowchart. No suffix on `/section` stays JSON |
| The development reader | `serve_reader(action, port)`. `start`, `stop`, or `status`. Binds `127.0.0.1`. `url` is `/view`. A stop ends only the recorded process |
| The section on either side | `query.beside(code, number)`. `previous` and `next` are section numbers in the tightest heading. A miss leaves both empty |

## Follow-ups

These are open. A count does not add a word to `forms`.

- Run `Indexer.index_stored_needles(workers=n)` before trusting stored `case`, `cut`, or `session` rows. That pass has not been run since those notes were added. Term rows and annotation rows are separate jobs. The SQLite connection only inserts and is not shared across threads. Do not call `index_pubinfos` or `reset`.
- The annotation table stores `code` only. Chapter, division, article, state, and federal frequencies cannot be computed until a member key for that scope is stored on the row.
- A raw annotation count follows the length of the code. Health and Safety, Government, and Education have the most rows. Evidence, the Constitution, and the Military and Veterans Code have the fewest. That count is not a rate.
- `Indexer.targets` folds case when it groups. Rows already stored still say `ET SEQ.` until the reindex. New annotations store `et seq.`
- Shared marks that are not forms yet: `the hearing`, `as amended`, `et seq.`, and the Administrative Procedure Act. A useful phrase is a candidate. It is not a new word class until a source names it.
- Noun titles (`Department`, `Office`, and the other `Noun` forms) have no stored needle rows.
- An office or court slug, and URL roots for an office, a court, a session law, the CFR, a rule, or a manual, were discussed and not added. A slug is the printed short form when one exists. Otherwise sanitize the printed name. Do not use the Python class name. Reporter abbreviations are not court slugs.
- `rank` and `common` still walk the token postings. Do not call them from a test. Phrase records from `document` are not stored.
- `/view` is the script-free reader. Jinja2 in `templates/` renders it. JSON stays on `/tree`, `/section`, and `/annotations` for the React client. `serve_reader` starts and stops that process for development.
- React is the client. It reads the JSON routes. The library is `/tree`, one level at a time. The reader is `/section`, the stored text beside the chart. Markup is `annotate` spans (`start`, `end`, `note`) drawn on that text. The DAG is the edge list from `refs.links()` and from `Diagram` (source, target, label), not only the mermaid string. Mermaid `flowchart TD` remains the static export. A clickable graph needs those edges so a node can open the next section. Do not use a timeline, a mindmap, a git graph, or a gantt chart. Stored graphs are codes, vesting, and enactments. The Jinja document stays available when scripts do not run.
