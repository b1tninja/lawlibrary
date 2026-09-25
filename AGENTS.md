# lawlibrary

Official statute and regulation text. Sacramento, California is home. Human setup is [README.md](README.md). The file layout is [docs/layout.md](docs/layout.md). Official words and the class that holds each one are [TERMS.md](TERMS.md).

## Axioms

These guide an agent that adds a parser, a pin, or a lookup.

1. **A closed set is an enum.** Reach for the member. `Cite.SECTION`, `Cite.RANGE`, `Cite.SERIES`. `Note.CITATION`, `Note.CROSS_REFERENCE`. `Clause.ENACTMENT`. `Canon.MANDATORY`. `Kind.AGENCY`, `Relation.DUTY`. `Instrument.STATUTE`, `Instrument.REGULATION`, `Instrument.RULE`, `Instrument.MANUAL`. `Branch.LEGISLATIVE`, `Article.I`. `Guide.CALIFORNIA_STYLE_MANUAL`. A constitution article is a `Provision`. A parser is `CanonMixin` and `StyleMixin`. A California code is a `Code` member. A citation span is `section`, `span`, or `series`. `Bench.TRIAL`, `Division.CIVIL`. `Function.REAL_ESTATE`. The value is the word a file may store. The loader turns that word back into the member before a caller sees it.

2. **A fact is a record.** A citation is a `Point`. A clause is a `Mark`. A canon hit is a `Signal`. A reference is an `Annotation`. A court book is a `Rulebook`. The open book is a `Context`. Fields stay on the record. A task reads `point.cite` and `point.numbers`.

3. **A repeated job is a helper.** Book identity is `resolve_book`. The open book is `document`. Marks on a sentence are `annotate`, `find_clauses`, `find_signals`, `find_mentions`. A section is `query.section`. A few sections for parser work are `sample.sample`. A pin is `analysis.pin`. A new call site uses the helper. It does not open Whoosh or a corpus file on its own.

4. **A new decision extends the record.** A new kind of citation, clause, canon, or office role is a new enum member and, when the words need a shape, a field on the record. A book abbreviation and a section number live in the data the helper already returns (`book`, `citation`, `numbers`).

5. **A miss stays a miss.** `found` is false and `reason` says why (`unknown_book`, `not_in_index`, `not_indexed`, `ordinance_absent`). The words of a section come from the index or from an official page that was opened.

6. **Two readings stay two readings.** When one sentence supports two canons that disagree, `ambiguities` reports both. The parser does not pick one.

7. **Reference legal text by looking up the citation.** A test, a specimen, and a note store the code and the section. The words come from `query.section`, or from an official page that was opened. Do not copy a sentence into the test, the module, or the note.

## Boundaries

- Commercial hosts (Justia, FindLaw, Westlaw, Lexis, Fastcase, Municode, American Legal, General Code, Barclays) are never sources.
- Quote a sentence only when it was retrieved from the local index or from an official page that was opened.
- Prefer plain text, then an XML-like file, then HTML, then PDF. A PDF of court rules stays a pointer until a text edition exists.
- Do not commit `data/`, zips, PDFs, or `.env`.
- Do not wipe `data/idx`.
