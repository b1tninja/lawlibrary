# Parser pitfalls

`structure.review` compares a citation-shaped phrase in a retrieved section with the link the parser recorded. Write the row here before changing the parser. A later cycle reads this list first.

A gap is one of three kinds:

| Gap | What it means |
| --- | --- |
| `short_title` | The link stopped at the first word "Code" while the sentence still names the book. |
| `unresolved` | The phrase names a book that is not one of the California codes. Leave it unresolved. |
| `unlinked` | The phrase was not recorded. |

The section number stays the printed text. The book is a `Code` member.

## Recorded

| Citation | Gap | What the parser did | What to avoid |
| --- | --- | --- | --- |
| Civil Code section 937 | `short_title` | "Section 411.35 of the Code of Civil Procedure" stopped at the first "Code", so the section was not `Code.CIVIL_PROCEDURE`. | Take the longest code title. "Code of Civil Procedure" is that book. |
| Civil Code section 1201 | `unlinked` | "Section 2093, Code of Civil Procedure" has a comma and no "of the", so the title was dropped. | A comma before a known title is the same book as "of the". |
| Civil Code section 1812.300 | `unresolved` | "Section 501(c)(3) of the Internal Revenue Code" was read as Civil Code section 501. The parenthetical sat between the number and the book. | An unknown title stays a miss. Do not assign it to the open book. |
| Civil Code section 1940 | `short_title` | "Section 7280 of the Revenue and Taxation Code" also matched section 728 of the open book. The number backtracked at the space before "of the". | A named code owns the whole span. Do not also file the number under the open book. |
| Revenue and Taxation Code section 7280 | `unlinked` | `(e)(1)(A)` on one line, and a colon list `(1)` … `(2)` … `or (3)`, stayed inside the parent. | A label opens a node at the start of a line, stacked against the previous label, or after a colon. A citation list such as "clause (i), (ii), or (iii)" does not. |
| Business and Professions Code section 11212 | `unlinked` | `(_l_)` and `(aa)` were swallowed by the previous subdivision. | A marked letter and a double letter are labels. |
| Fish and Game Code section 8597 | `unlinked` | "Section 8598.2, and unless otherwise prohibited in this code" was called a citation because a comma and the word "code" looked like a title. | A comma introduces a book only when a known code title follows. |
| Revenue and Taxation Code section 7280 | `unlinked` | "Chapter 257 of the Statutes of 1985" was dropped. The same shape appears in Welfare and Institutions Code section 14043.26 and Fish and Game Code section 8681.5. | Record the chapter and the year. It is not a code section, so it is not followed as one. |
| Labor Code section 3352 | `unresolved` | "Section 101(6) of the Internal Revenue Code" names a federal title. Civil Code section 1812.300 has the same title. | Keep the phrase and leave the book empty. Do not assign the open code. |
| California Constitution | `unlinked` | "Section 8 of Article XVI" and "Sections 8 and 9 of Article II" were read as ordinary section numbers. The same number is used in more than one article. | Keep the article with the section. Do not look the number up alone. |
| Civil Code section 1375 | `unlinked` | "Sections 1119 to 1124" and "Sections 2953.1 through 2953.4" kept only the first number, and `through` parsed as a series. | A range is one citation. `through` prints and parses as `to`. |
| Government Code section 11370 | `unlinked` | "commencing with Section 11340" stored the start and dropped the open end. | An open California span prints `commencing with Section`. Indigo Book R5.2.3 forbids `et seq.` for a span. `et seq.` still parses, and prints back as commencing. |
| Civil Code section 1940 | `unlinked` | "this chapter" kept the word and not the chapter that contains the section. | Resolve the unit from the heading. The relative words stay the link text. |
| Revenue and Taxation Code section 12208 | `unlinked` | "Section 28 of Article XIII" rendered as a subdivision of section 28. Article XIII A did not parse. | The article is outside the section: `California Constitution, article XIII A, section 4`. |
| Water Code section 12872 | `unlinked` | "subdivision (b)(1) of Section 12867" dropped `(1)`. "paragraph (1) of subdivision (b)" became two subdivisions. | A stack is one chain. `(a) and (b)` stays two siblings. |
| Probate Code section 16461 | `unresolved` | "YEAR PERIOD PROVIDED IN SECTION 16460" took the capital words in front of Section as the book. | A code prefix includes the word Code. Other words stay outside the citation. |
| Code of Civil Procedure section 1161 | `short_title` | "Section 1946 of the Civil Code" was recorded, then the words after that title were read as a longer book name. | A known title ends the book. Later words are not a longer title unless a longer known title actually continues. |

## Open

No open gaps.
