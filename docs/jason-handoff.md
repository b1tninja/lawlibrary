# Handoff: query interface for Jason

Jason is a virtual agent for the manager of Mystique Community Association, a common interest development in Sacramento, California. It needs official statute text. It must not invent a quotation, and it must not scrape leginfo during a task.

lawlibrary already stores the Legislature’s pubinfo files and answers `list_codes`, `list_sessions`, `search_law`, and `get_section` over the local Whoosh index (`indexer.Indexer`, `mcp_server.py`). Those four calls are the floor. This page is the interface Jason should be able to call. Implement it in lawlibrary. Do not import Jason, PayHOA, or Mystique facts into this package.

## Place

Every query is scoped.

| Field | Value for Mystique | Meaning |
| --- | --- | --- |
| `country` | `US` | ISO 3166-1 |
| `region` | `US-CA` | California statutes. This is the index. |
| `locality` | `Sacramento` | City and county. Ordinances are not in the index. |
| `session` | newest, unless the caller names a year or `all` | Same rule as `search_law` today. |

`locality="Sacramento"` does not switch the corpus to a city code. Davis-Stirling and the Business and Professions Code are state law. A query that asks for a Sacramento ordinance returns a structured miss: the locality is known, the ordinance text is not in this index, and no commercial host is fetched. Do not invent municipal section numbers.

## What Jason asks

The manager index in Jason (`docs/community-manager.md`) cites these bodies. The interface should answer each of them without the caller knowing Whoosh.

| Ask | Citation the caller has | Shape |
| --- | --- | --- |
| One section | `CIV 5806`, `Civil Code § 5806`, `BPC 11500` | Full active text, heading path, citation, session |
| One subdivision | `BPC 11500(d)`, `Civ. Code § 5800(a)(4)` | The section, plus the requested subdivision label. The text is the official section. Do not split the section into a fake document if the index stores one row per section. |
| A span | `CIV 4000-6150`, `BPC 11500-11506` | An outline, not the concatenated text |
| A named act | `davis-stirling`, `cid-manager` | The same outline as the span it names |
| Words inside a span | fidelity, inside Civil Code 5800–5810 | Hits limited to that code and that numeric span |
| Sacramento local law | a parking or building ordinance | A miss, with `region` still available for the state code |

Named spans, current through the 2026-09-24 manager index:

| Name | Code | Sections | Why Jason has it |
| --- | --- | --- | --- |
| `davis-stirling` | `CIV` | 4000–6150 | Common Interest Development Act |
| `cid-manager` | `BPC` | 11500–11506 | Certified common interest development manager |
| `mutual-benefit` | `CORP` | 7110–8910 | Nonprofit Mutual Benefit Corporation Law. Outline only. Never return this span as text. |

`mutual-benefit` is large. `outline` is the only default. A caller who wants one section uses `section`.

## Calls

One module, used by the CLI and by MCP. Names below are the contract. Return dicts and lists the MCP layer can serialize. Empty input is a miss, not an exception that dumps a traceback to the agent. An unknown code, a section that is not in the index, and a Sacramento ordinance are misses with a `reason`.

```text
place(locality="Sacramento") -> {
  country: "US",
  region: "US-CA",
  locality: "Sacramento",
  statutes: "US-CA",
  ordinances: "absent"
}

section(code, number, *, subdivision=None, session=None) -> {
  citation, code, section, subdivision,
  title, path: [{level, heading}, ...],
  text, session, active
}

outline(code, start, end, *, session=None) -> {
  code, start, end, session,
  nodes: [{level, heading, first, last, count}, ...]
}

range(code, start, end, *, session=None, text=False) -> outline, or sections if text and the span is at most 30 sections

search(query, *, code=None, start=None, end=None, limit=10, session=None) -> [
  {citation, code, section, path, snippet, session}, ...
]

act(name, *, session=None) -> outline for a named span

cite(expression, *, session=None) -> section, outline, or miss
```

`cite` accepts the forms Jason actually writes:

- `CIV 5806`
- `Civil Code section 5806`
- `Civ. Code § 5806(a)`
- `BPC 11500(d)`
- `CIV 4000-6150`
- `Business and Professions Code §§ 11500-11506`
- `davis-stirling`

A span expression returns `outline`. A single section returns `section`. A named act returns `act`.

## Outline shape

Heading fields already stored on each section are `DIVISION`, `TITLE`, `PART`, `CHAPTER`, `ARTICLE` and their `*_HEADING` values. Group consecutive sections that share a heading. A node records the first and last section number in that group, not a copy of the text.

For `CIV 4000-6150` the caller should be able to see Chapter 9 (insurance, 5800–5810) and Article 9 (managing agent, 5375–5385) without reading every section. Order nodes as the code orders them: division, title, part, chapter, article. Skip a level whose heading is empty.

Section numbers are not integers. `5375.5` sits between `5375` and `5376`. Compare with a numeric key: split on `.`, then compare each component as an integer. A trailing letter, if one appears, sorts after the same number with no letter. `SECTION_NUM` is a Whoosh `ID`. Filter in Python after restricting the query to `LAW_CODE`. Do not require a reindex to ship the range filter.

`range(..., text=True)` returns full text only when `count <= 30`. Above that, return the outline and `reason: "span too large for text"`. `BPC 11500-11506` qualifies. `CIV 4000-6150` does not.

## Search

`search_law` stays the unscoped full-text call. `search` adds optional `code`, `start`, and `end`. The text query still runs through the existing parser, including the citation shortcut. The span is a filter, not a second query language. Hits outside the span are dropped. `limit` applies after the filter, so ask Whoosh for more than `limit` when a span is set, then trim.

Do not search Sacramento ordinances. There is nothing to rank.

## Misses

```text
{ "found": false, "reason": "not_in_index" | "unknown_code" | "ordinance_absent" | "unknown_act" | "span_too_large",
  "expression": "<what the caller passed>" }
```

`found: true` on successes, so the caller does not treat an outline of zero nodes as a statute.

## MCP

Add tools beside the existing four. Keep the old tools. New tools:

| Tool | Calls |
| --- | --- |
| `place` | `place` |
| `cite_law` | `cite` |
| `outline_law` | `outline` |
| `search_span` | `search` |

`get_section` remains the single-section tool. `cite_law` may return either a section or an outline; the payload includes `kind: "section" | "outline" | "miss"`.

## Tests

Parser tests do not need an index: each citation form above, the numeric ordering of `5375`, `5375.5`, and `5376`, and a Sacramento ordinance expression resolving to `ordinance_absent`.

Index tests skip when `data/idx` is missing. When it is present, `cite("CIV 4000")` returns text, `outline("CIV", "5800", "5810")` includes a heading and does not include section 1940, and `act("davis-stirling")` reports a span of 4000–6150.

## Out of scope

- Downloading pubinfo zips, or crawling Municode, American Legal, or the City of Sacramento.
- Federal statutes (Fair Housing Act, ADA, NFIP). Say they are outside `US-CA` rather than searching the California index for them.
- Quoting a section into a Mystique governing document. Jason does that, and only from `text` this interface returned.
- Changing Whoosh schema field types in this pass.
