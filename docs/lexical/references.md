# Cross-references as index keys

A citation names a section. A cross-reference points at another place in the same book, or at another book. `citations.annotate` marks both. The mark's `target` is the index key used to look the place up. The surface shorthand (`Civ. Code`, `§`, `sections`) is not the key.

The section-sign grammar and point-of-authority signals are in [citations.md](citations.md). Sampling a book that is missing from disk is in [sample.md](sample.md).

## Book identity

`resolve_book` maps every title and shorthand to one abbreviation from the catalog (`{"CIV": "Civil Code - CIV"}`). `Civil Code`, `Civ. Code`, `CIV`, and `California Civil Code` are the same book. `Bus. & Prof. Code` and `Business and Professions Code` are `BPC`. The key always stores that abbreviation, never the words the writer used.

`document(code, section, books=…)` is the open code and section. Inside that context:

| Surface words | Resolved target |
| --- | --- |
| `this code` | The open abbreviation alone (`CIV`) |
| A bare `section` / `§` number | `{ABBR} {number}` (`CIV 1940`) |
| `the following` | `{ABBR} the following` — stays in the open section |

## Index key shapes

| Kind | `Cite` / `Note` | Index key | Example |
| --- | --- | --- | --- |
| One section | `Cite.SECTION` / `Note.CITATION` | `{ABBR} {number}` | `CIV 1940`, `BPC 10080` |
| Subdivision | same | `{ABBR} {number}(letter)` | `CIV 5806(a)` |
| Range (`§§` / `sections` joined by a dash or `to`) | `Cite.RANGE` | `{ABBR} {first}-{last}` | `CIV 4000-6150` |
| Series (`§§` / `sections` joined by commas or `and`) | `Cite.SERIES` | `{ABBR} {n}, {n}, …` | `GOV 11340, 11370` |
| Structural pointer | `Note.CROSS_REFERENCE` | `{ABBR} this {unit}` | `BPC this part`, `CIV this chapter` |
| Commencing span | `Note.CROSS_REFERENCE` | `{ABBR} commencing with Section {n}` | `BPC commencing with Section 11000` |
| Open-section pointer | `Note.CROSS_REFERENCE` | `{ABBR} the following` | `BPC the following` |
| Whole open code | `Note.CROSS_REFERENCE` | `{ABBR}` | `CIV` |
| Named act | `Note.NAMED_ACT` | The act title as written | `Administrative Procedure Act` |
| Federal statute | (external) | `{title} USC {section}` | `28 USC 1` |
| Federal regulation | (external) | `{title} CFR {section}` | `24 CFR 1.1` |

A range and a series are different keys. `CIV 4000-6150` is one span. `GOV 11340, 11370` is two separate sections. Lookup follows that: `query.search` opens a range from the first number through the last, and opens each number of a series.

## Internal vs external

**Internal** references stay inside the open book. They use the structural words or a number that the context supplies:

- `this part`, `this chapter`, `this division`, `this article`, `this title`, `this code`
- `commencing with Section` plus a number
- `the following`
- A bare section number while `document` is open

**External** citations name another publication: another California code, the United States Code, or the C.F.R. Their key uses that other book's abbreviation or the federal title form above, not the open book's abbreviation.

## Lookup and misses

The key is resolved only through `query.section` or `query.search` when that book is indexed.

| Book | Where the words live | Miss |
| --- | --- | --- |
| California code (`CIV`, `BPC`, …) | Whoosh index (`data/idx`) | `not_in_index` when the index or section is absent; `unknown_code` when the abbreviation is not in the catalog |
| One CFR title | `data/codes/US/cfr/{title}.sqlite` (`corpus.cfr_corpus_path`) | `not_in_index` when that file is absent |
| United States Code | `data/codes/US.sqlite` | `not_in_index` when that file is absent |
| Court rule | Pointer only (`url`, `shape`) until words exist | `not_indexed` |

`corpus` keeps one SQLite file per publication. A missing file is left detached. It is not invented and it is not downloaded.

`query.cite` parses a whole citation string (`Civ. Code § 5806`, `CIV 4000-6150`) and hands it to `section`, `outline`, or `act`. That path uses the same abbreviations and misses.

## Pins are not the statute

`analysis.pin` stores a jurisdiction or delegation fact for one registered class, taken from one citation. Re-pinning that citation replaces the earlier rows. The statute text stays in its corpus. A pin is not a copy of the section.

## Examples from the index

Business and Professions Code section 10080 (local index). Internal keys are `BPC this part`, `BPC commencing with Section 11000`, and `BPC this division`. The Administrative Procedure Act is a named act, not a section key:

> The commissioner may adopt, amend, or repeal rules and regulations that are reasonably necessary for the enforcement of the provisions of this part and of Chapter 1 (commencing with Section 11000) of Part 2 of this division. The rules and regulations shall be adopted, amended, or repealed in accordance with the provisions of the Administrative Procedure Act.

Civil Code section 1940 (local index). Internal keys include `CIV this chapter` and `CIV the following`. The Revenue and Taxation Code and the Health and Safety Code are external books:

> (a) Except as provided in subdivision (b), this chapter shall apply to all persons who hire dwelling units located within this state including tenants, lessees, boarders, lodgers, and others, however denominated.

> (b) The term "persons who hire" shall not include a person who maintains either of the following:

> (1) Transient occupancy in a hotel, motel, residence club, or other facility when the transient occupancy is or would be subject to tax under Section 7280 of the Revenue and Taxation Code.

> (E) Food service provided by a food establishment, as defined in Section 113780 of the Health and Safety Code, located on or adjacent to the premises of the hotel or motel…
