# The tree

How a code is shaped, where that shape is kept, and how it is read. This is
the strategy behind `toc_trail`, `TOC_PATH`, `law_tree`, `node/…` addresses
and `expand=all`. An agent adding a tree walk, a breadcrumb, a contents
list, or an aggregate by heading starts here.

## The rule

**Do not infer structure from the unit fields. Store the publisher's tree
and read it.**

`DIVISION`, `TITLE`, `PART`, `CHAPTER` and `ARTICLE` on a section are the
numbers of its ancestors, not a nesting. California's codes do not share one
nesting, and no code follows the order those five names suggest.

| Code | How it nests (dominant edges, from `LAW_TOC_TBL`) |
| --- | --- |
| CIV | division > part > title > chapter > article; title > article |
| PEN | part > title > chapter (most often); title > division > chapter |
| GOV, CORP, EDC | title > division > part > chapter |
| HSC, RTC, WIC | division > part > chapter > article |
| VEH, FIN, COM | division > chapter > article; VEH also division > article |

Units skip levels freely. Nearly every code opens with headings that have no
number at all — GENERAL PROVISIONS, PRELIMINARY PROVISIONS, TITLE OF THE ACT
— and 706 sections sit under them. A walk over five fields in a fixed order
cannot reach those, files 379 captions under the wrong unit, lists two
Title 1s under one division as one rung, and sorts Part 2.52 after Part 2.9.

## What the publisher ships

`LAW_TOC_TBL` is the tree the official site draws, one row per heading:

| Column | What it is |
| --- | --- |
| `NODE_TREEPATH` | The path, as a tuple: `(6, 8, 1)`. A child's path extends its parent's. |
| `NODE_LEVEL` | Depth, from 1. |
| `NODE_POSITION` | Order among siblings. This is the order, not a sort of the numbers. |
| `HEADING` | The caption, with the publisher's range: `DIVISION 1. PERSONS [38. - 86.]`. |
| `CONTAINS_LAW_SECTIONS` | Whether sections hang directly here. |
| the five unit fields | The ancestors' numbers repeated on the row. |

`LAW_TOC_SECTIONS_TBL` places every section on a node by
`LAW_SECTION_VERSION_ID`. That join places all 162,431 sections of
`pubinfo_2025`; there is no unplaceable section.

**The unit a row is** is the field it fills that its parent does not
(`own_unit`). A row that adds no field is unnumbered. In all 24,386 rows
this agrees with the caption's own first word — zero disagreements — which
is why reading the caption back also works when only the section is in hand.

## What is stored on a section

`toc_trail` walks the path prefixes and keeps every ancestor as a rung; the
section stores the result (`c473273`):

| Field | Holds |
| --- | --- |
| `TOC_PATH` | The node's path as text, `6.8.1`. A prefix names a subtree. |
| `TOC_LEVEL`, `TOC_POSITION` | Depth and sibling order. |
| `TOC_UNIT` | The node's own unit, or `unnumbered`. |
| `TOC_TRAIL` | Every rung: `unit`, `number`, `heading`, `position`, `path`, `holds`. |

The five `*_HEADING` fields are still written, and each now carries the
caption of the unit its row is, not the deepest field in a fixed order.

## How it is read

**Address a node by its path.** `us-ca/civ/node/6.8` is one node. A
numbered address, `us-ca/civ/division/3`, is a filter on unit fields that can
name several nodes at once; it keeps the walk it always had, so nothing that
resolved before resolves differently.

**Children of a node** are the distinct rung one step below it across the
sections under it, in `position` order — `_tree_from_trails`. A node that
holds sections and has no rung below lists its sections.

**The whole tree** is the same pass, walking each trail below the node once
and placing each rung by its path — `_forest_from_trails`, given as `tree`
when asked with `expand=all` (route) or `expand=True` (`law_tree`,
`tree_law`). Headings only, as the Legislature's expanded view draws it.

**Crumbs** above a node are the node's trail, each rung named by its caption,
or its unit and number, or its heading when it has neither.

**Ordering** without a stored position: a heading number is a decimal — 2.52
sits between 2.5 and 2.6 — and a section number is not — 1738.10 follows
1738.9. `heading_key` and `section_key` are the two keys; a rung says which.

## Where a reader falls back

An index built before the trail was stored has no `TOC_PATH`. There the code
root and numbered addresses keep the old walk, with captions read back from
their own words (`_captions`), and a `node` address is a miss that says
`not_in_index`. The tree draws in full only from an index built after
`c473273`. Whoosh will not add fields to an existing index: an incremental
add against an older index raises `UnknownFieldError`, so moving to the tree
is a rebuild.

## Aggregates

A count by heading is the ledger (`ledger.py`). A **place** is one leaf of
the publisher's tree — the node a section hangs from, or in an index built
before the trail, one cell of the ladder — and a section sits at exactly
one place. The ledger stores each word's count at each place, built once
per index generation over the newest edition only, in parallel: the seats
are read in document slices and the lexicon is walked in term ranges, one
worker per processor. On the full index that is 162,431 sections, 20,381
places, 4.3 million rows, about two minutes on 32 workers; the single-thread
walk it replaces took five minutes and kept nothing.

A scope is a set of places and its count is a sum: `Scope.CODE('CIV')`,
`Scope.CHAPTER('CIV 2')` (every Chapter 2 in the code, by number),
`Scope.NODE('CIV 6.8')` (one place and everything under it, by path prefix),
`Scope.STATE('US-CA')`. `weight.rank` and `weight.common` read it; the MCP
tool `common_terms` takes `node` as a scope. The node scope is empty until
the index carries `TOC_PATH`. A new call site that counts words by heading
opens the ledger; it does not walk the lexicon or join the needle store by
`IN` lists.

## Sources

The official table of contents: `https://leginfo.legislature.ca.gov/faces/codesTOCSelected.xhtml?tocCode=CIV`,
and expanded: `codedisplayexpand.xhtml?tocCode=CIV`. The data: `LAW_TOC_TBL`
and `LAW_TOC_SECTIONS_TBL` in each `pubinfo_YYYY.zip`, documented only as
tables in `pubinfo_load.zip`; see [caml.md](caml.md) for what the state does
and does not publish.
