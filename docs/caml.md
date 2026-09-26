# CAML

The markup California publishes its statutes and bills in. Every section in a
`pubinfo_YYYY.zip` is one CAML document, stored as a `.lob` file beside the
row that names it.

`caml.py` is the model. `caml.parse` gives the tree, `caml.words` gives the
reading.

## What the state publishes

| Thing | Where |
| --- | --- |
| The data | `https://downloads.leginfo.legislature.ca.gov/` |
| The distribution readme | `pubinfo_Readme.pdf`, `pubinfo_Readme.txt` |
| Changes to the distribution | `pubinfo_News.pdf`, `pubinfo_News.txt` (last entry 2016-02-12) |
| The relational schema | `pubinfo_load.zip` — `capublic.sql` and one SQL\*Loader control file per table |
| A schema for CAML itself | **nothing** |

The readme documents the container: 18 tab-delimited tables, fields
`TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '` + "`" + `'`, one `.lob` per row that has
one. `law_section_tbl.sql` loads the LOB into a column the state names
`content_xml`, and `capublic.sql` declares that table `CHARACTER SET utf8`.
None of the 37 files in the download directory is an XSD or a DTD.

CAML names its own schema and does not ship it. Every bill document carries:

```
xsi:schemaLocation="http://lc.ca.gov/legalservices/schemas/caml.1# xca.1.xsd"
```

`xca.1.xsd` is a bare relative filename that is not distributed, and
`lc.ca.gov` no longer resolves and has no Wayback snapshot. So the grammar
below is not quoted from a specification. It is the one the corpus shows.

Documents carry `<!-- Copyright © Legislative Counsel Bureau, State of
California. -->`.

## How the grammar was found

Every `LAW_SECTION_TBL_*.lob` in `pubinfo_2025.zip` was parsed as XML and its
parent-to-child element edges counted.

| | |
| --- | --- |
| Documents | 162,431 |
| Parse failures | 0 |
| Roots | `caml:Content`, all of them |
| Distinct element edges | 56 |
| Distinct document shapes | 314 |
| Elements | 23 |
| `span` classes | 10 |

Two shapes are almost the whole corpus: a run of `p`, and a run of `p` holding
`span`.

## Elements

Six are California's own. The rest are borrowed from XHTML and keep their
shape, though not always their meaning.

| Element | `caml.Element` | What it is |
| --- | --- | --- |
| `caml:Content` | `DOCUMENT` | The root. One per section. |
| `caml:Fraction` | `FRACTION` | A vulgar fraction, holding the two below. |
| `caml:Numerator` | `NUMERATOR` | The number above the line. |
| `caml:Denominator` | `DENOMINATOR` | The number below it. |
| `caml:LabelledField` | `FIELD` | A blank on a form, with the caption to write against. |
| `caml:TipIn` | `INSERT` | A plate bound into the printed volume. `numPages` says how many. No words. |
| `p` | `PARAGRAPH` | A block. 684,984 of them. |
| `span` | `SPAN` | Not an HTML span. See below. |
| `br` | `BREAK` | A line within a block. |
| `h1` | `HEADING` | A heading inside a section. |
| `table` `thead` `tbody` `tr` `td` `th` `colgroup` `col` | `TABLE` `HEAD` `BODY` `ROW` `CELL` `HEADER` `COLUMNS` `COLUMN` | A table, as in XHTML. |
| `i` `b` `u` `sub` `sup` | `ITALIC` `BOLD` `UNDERLINE` `SUBSCRIPT` `SUPERSCRIPT` | Type. |

## A span is not a span

This is the one thing that makes CAML unreadable as HTML. Across the corpus a
`span` is **empty 599,451 times and carries words 190 times**. An empty span
is not a wrapper around anything — it is a character, or a rule ruled across a
form. Its class says which.

| Class | `caml.Glyph` | Count | Reads as |
| --- | --- | --- | --- |
| `EnSpace` | `EN_SPACE` | 582,196 | a space |
| `EmSpace` | `EM_SPACE` | 6,979 | a space |
| `ThinSpace` | `THIN_SPACE` | 1,998 | a space |
| `NbSpace` | `NB_SPACE` | 1 | a space |
| `DottedLeaders` | `DOTTED_LEADERS` | 5,656 | nothing |
| `UnderlinedLeaders` | `UNDERLINED_LEADERS` | 1,400 | nothing |
| `SpacedLeaders` | `SPACED_LEADERS` | 1,258 | nothing |
| `DashedLeaders` | `DASHED_LEADERS` | 21 | nothing |
| `SmallCaps` | `SMALL_CAPS` | 180 | its words |
| `SpecialFormatting` | `SPECIAL_FORMATTING` | 42 | its words |

En, em, thin and non-breaking are widths. A width is not a word, so each one
reads as a single space; keeping the typographic codepoints would only split a
search in two.

## What flattening costs

An HTML reader drops an empty element, knows nothing of a fraction, and writes
Markdown where the statute had type. All three losses are in the index today.

| CAML | Read as HTML | Read as CAML | In the index |
| --- | --- | --- | --- |
| `(a)<span class="EnSpace"/>No franchisor` | `(a)No franchisor` | `(a) No franchisor` | most sections |
| `Article XIII<span class="ThinSpace"/>B` | `Article XIIIB` | `Article XIII B` | |
| `33<caml:Fraction>1/3</caml:Fraction> percent` | `3313 percent` | `33 1/3 percent` | 28 sections carry `3313` |
| `Section 1902(<i>l</i>)(3)` | `Section 1902(_l_)(3)` | `Section 1902(l)(3)` | 831 sections carry `_l_` |

The last two are not cosmetic. A third read as three thousand percent is a
different voting threshold, and a subdivision written `(_l_)` is neither the
subdivision a reader searches for nor the one a citation parser can resolve.

## Checking the model against the corpus

Every section of `pubinfo_2025` was parsed with `caml.py` and with the
indexer's `html2text`, and the two readings compared.

| | |
| --- | --- |
| Documents | 162,431 |
| Parse failures | 0 |
| Tags or classes the grammar did not cover | 0 |
| Readings identical | 97,212 |
| Differ by spacing | 62,927 |
| Differ inside a table | 664 |
| Differ in their words | 1,628 |

Each of the 1,628 was attributed: 1,040 are italics written as Markdown, 234 a
fraction, 240 a table as well, one small caps. In none of them does the CAML
reading lose a word the flattened one keeps.

The indexer still reads CAML with `html2text`; `caml.py` does not replace it.
Changing what is stored means building the index again.

## Reading the model

`parse` returns a `Document`: a tree of `Piece`, and `unknown`, which names
any tag or span class the survey had not met. It is empty for all 162,431
sections of `pubinfo_2025`. A later edition that adds an element says so there
rather than losing the words.

```python
import caml

doc = caml.parse(lob)
caml.words(doc)     # the reading
caml.glyphs(doc)    # how many of each glyph it sets
doc.unknown         # what the grammar did not cover
```
