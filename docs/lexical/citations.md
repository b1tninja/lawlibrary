# Section signs and points of authority

A citation is how a sentence names the statute it relies on. `citations.py` finds those names inside prose. `query.parse_citation` still parses a citation that is the whole query (`Civ. Code § 5806`, `CIV 4000-6150`).

## The sign

| Sign | What follows | `Cite` value |
| --- | --- | --- |
| `§` or `section` | One section number, optionally a subdivision such as `(a)` | `section` |
| `§§` or `sections`, joined by a dash or by `to` | A range | `range` |
| `§§` or `sections`, separated by commas or by `and` | A series | `series` |

`§` is not the start of `§§`. The double sign is read first.

`28 U.S.C. § 1` is one section. `28 U.S.C. §§ 2071–2077` is a range. `Gov. Code §§ 11340, 11370` is a series. Those shapes appear in the court notes already written from official pages.

## A point of authority

The point of authority is the citation offered for a statement. The words in front of it are a signal, not the source:

| Signal | Role |
| --- | --- |
| `see` | The cited section supports the statement, sometimes after an inference |
| `see also` | An additional supporting section |
| `cf.` | A section that is analogous; the comparison is the writer's |
| `but see` | A section that points the other way |
| `accord` | Another section that agrees |
| `contra` | A section that disagrees |
| `e.g.` | An example, not the only section |

California Rules of Court, rule 1.200, requires a document filed in a California court to follow either the California Style Manual or The Bluebook, and to use one of them consistently. Both manuals use the section sign. The Style Manual is not posted in full on `courts.ca.gov`, so the parser is built from the sign and from the citation shapes in the official pages we have, not from a scanned copy of the manual.

`document` is the book being read. Inside it, `this code` means that book, a bare `section` number is a section of that book, and `the following` stays in the open section. `resolve_book` treats `Civil Code`, `Civ. Code`, `CIV`, and `California Civil Code` as one abbreviation. The catalog is the index map of titles, such as `Civil Code - CIV`.

`annotate` keeps four kinds of mark. A `citation` is a section sign or the word "section" plus a number. A `cross_reference` is "this part" or "commencing with Section" plus a number. A `named_act` is a statute named by its title, including the Administrative Procedure Act. A `short_form` is `id.`, `supra`, or `et seq.` Rule 1.200 requires the California Style Manual or The Bluebook. Neither manual is copied here. These are the shapes those manuals share.

A signal on a `Point` is the word that introduced it. The numbers are what a search opens. `query.search` reads a `§` or `§§` citation in the query and returns those sections instead of a word search. A range uses the first and last numbers. A series opens each number. A query with no section sign is unchanged.
