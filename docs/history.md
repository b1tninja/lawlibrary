# Section history and succession

How a California section changed from one edition on the shelf to the next, and which section continues a former one. `history.py` reads the shelf. `succession.py` reads the California Law Revision Commission's tables and Comments. Both answer with records and enum members; a miss is `found: false` with a `reason`.

## What the shelf can tell

The shelf (`data/shelf/<year>/`) holds one index per session file. From 2011 on an edition carries the code tables: each section in force when the Legislature last refreshed that session's zip, and the history note the table printed beside it. Editions before 2011 carry bills, not code sections; `section_history` reports them as `not_indexed`.

- An edition is a snapshot, not a day. `pubinfo_2013.zip` was refreshed through 2014, so CIV 1363 (repealed operative January 1, 2014) is in the 2011 edition and absent from the 2013 one.
- A note names only the **latest** act on the section. An act between two editions that a later act overwrote is not on the shelf. The 2013 edition's note for CIV 4525 names Stats. 2013, Ch. 183 (SB 745), not the chapter that first added it.
- A repeal leaves no note. The section is absent from the next edition. A `REPEALED` step names a statute only when a `Recodification` on record covers the span (`recodification` on the step, `basis: recodification`).
- One row per section number per edition is read. A section with two versions in one edition (one operative later) keeps the first the index returns.

## `history`

| Name | What it is |
| --- | --- |
| `HistoryNote` | One history note read: `action` (`needles.Action`), `statute` (`needles.Session`: year, chapter, the enrolled bill's section), `bill`, `measure` (Code Amendments, an initiative), `renumbered_from`, `dates` (`Dated`: `needles.Occasion` and the day). `read` is false when the first clause did not parse; `note` keeps the printed words. |
| `read_note(note)` | The note's clauses split on runs of spaces: action and credit first, then a bill label in parentheses, then `Effective`, `Operative`, `Inoperative`, `Repealed as of`. |
| `Change` | `ADDED`, `AMENDED` (the later note names another act), `REVISED` (words differ, same act named), `RENOTED` (same words and act, the note's print changed; a bill label added in 2017, for one), `UNCHANGED`, `REPEALED`. |
| `Diff` | Word-level counts (`inserted`, `deleted`, `replaced`), `ratio`, and at most six `Hunk`s of fourteen words a side, each with the cut label printed before it (`near`). `summary()` is one line. |
| `section_history(code, number)` | Every edition: `found`, `digest`, `words`, `credit`. `steps` between code editions. `credits`: each distinct act named, oldest first. |
| `changes(code, spans, since=, until=, act=, unchanged=)` | Every step in the spans as one list, oldest first. `act='davis-stirling'` adds `1350-1378` and `4000-6150`. `UNCHANGED` and `RENOTED` are left out unless `unchanged=True`. |
| `between(code, spans, before, after)` | Two editions compared directly. |

## `succession`

The Davis-Stirling recodification (Stats. 2012, Ch. 180, AB 805; operative January 1, 2014) repealed Civil Code 1350-1378 and added 4000-6150. The Commercial and Industrial Common Interest Development Act (Stats. 2013, Ch. 605, SB 752) continued part of the same former law in 6500-6876. The Commission's documents, from <http://www.clrc.ca.gov/H855.html> and <http://www.clrc.ca.gov/Menu3_reports/publishers.html>:

| `Report` | Document | Read as |
| --- | --- | --- |
| `AB805_DISPOSITION` | `pub/publishers/2012/AB805DispoTable.pdf`, the disposition table for Ch. 180 | `Source.DISPOSITION_TABLE` rows: the pin |
| `SB752_DISPOSITION` | `pub/publishers/2013/SB752DispoTable.docx`: the disposition table for Ch. 605, then a table of similar provisions in 4000-6150 | table rows; the second table is `PARALLEL` |
| `RECOMMENDATION_2011` | `pub/Printed-Reports/Pub235-H855.pdf`, 40 Cal. L. Revision Comm'n Reports 235: the proposed legislation and a Commission Comment on each new section | `Source.COMMISSION_COMMENT` rows |
| `CLEANUP_2012`, `CLEANUP_2013` | the clean-up recommendations | fetched, not yet read |

`fetch()` (`python ca.py --fetch-clrc`) saves them in `data/clrc` (not committed) and turns a PDF into text beside it with `pdftotext` (`PDFTOTEXT` names another binary). Without the files a lookup is `not_fetched`; without the text, `not_extracted`.

| Name | What it is |
| --- | --- |
| `Succession` | `CONTINUED` (a table row: where, not how), `CONTINUED_WITHOUT_CHANGE`, `CONTINUED_WITHOUT_SUBSTANTIVE_CHANGE` (`continues the substance of`, or only nonsubstantive changes listed), `CONTINUED_WITH_CHANGES` (a substantive change listed), `RESTATED`, `GENERALIZED`, `SUPERSEDED`, `SIMILAR`, `NEW`, `OMITTED`, `OMITTED_SEE`, `NOT_CONTINUED`, `PARALLEL`, `CANDIDATE` |
| `Shape` | `ONE_TO_ONE`, `SPLIT` (the former section went to several), `COMBINED` (the target came from several), `SPLIT_AND_COMBINED` |
| `Source` | `DISPOSITION_TABLE`, `COMMISSION_COMMENT`, `SIMILARITY` |
| `Provision` | code, section, and the part as printed (`(e)(3) (except last ¶)`); `path` and `tops()` are its labels |
| `Row` | `former`, `targets`, `succession`, `shape`, `source`, `report` (URL, page or line), `see`, `act`, `score` |
| `Recodification` | `DAVIS_STIRLING`, `COMMERCIAL_AND_INDUSTRIAL`: spans, chapter, bill, the documents. The operative day is read from the new sections' notes. |
| `successors(code, number, subdivision=None)` | Table rows, then Comment rows naming the former provision, then similarity candidates only for an act whose table names no row for the section. `targets`: each named section in the newest edition with its latest act. |
| `predecessors(code, number)` | The reverse, plus `PARALLEL` rows and candidates when no official row names a former provision. |
| `coverage(act)` | Former sections and top-level subdivisions (from `structure.split_nodes` on the last edition carrying them): placed by a continuing row, only omitted, or unplaced with candidates; new sections the table, a `see`, the Comments, or neither account for. |

The recommendation predates the bill's last amendments, so a Comment can disagree with the enacted table; both rows are returned and neither is dropped. A similarity candidate is TF-IDF cosine over words and word pairs, between the last edition carrying the former section and the first carrying the new span. It is never a pin.

## Command and tools

```bash
python ca.py --history CIV 1363
python ca.py --changes CIV 4000 6150 1350 1378 --since 2011
python ca.py --changes CIV --act davis-stirling
python ca.py --changes CIV 4000 6150 --between 2023 2025
python ca.py --successors CIV 1363 "(g)"
python ca.py --predecessors CIV 5855
python ca.py --coverage davis-stirling
python ca.py --fetch-clrc
```

MCP: `section_history`, `law_changes`, `successor_sections`, `predecessor_sections`, `recodification_coverage`.
