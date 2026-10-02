# Layout

Sacramento, California, USA is the home jurisdiction. `python ca.py` is that place. The rest of the tree is other governments, added only when an official publication exists.

## Packages

| Path | What it is |
| --- | --- |
| `core.py` | Package root, the data archive, the Whoosh index, and the SQLite corpus directory. The shelf — one index per edition under `data/shelf/<year>/`, built at once and read as one — is `core.open_index`. |
| `ca.py` | The command. It calls `us.ca`. |
| `us/ca/` | California: the state, its editions (codes from 2011, bills from 1989), the shelf build, and `main`. |
| `us/ca/apa.py` | The California codes, `Code`. |
| `us/ca/caml.py` | CAML, the markup California publishes statutes in. The grammar is in [caml.md](caml.md). |
| `us/ca/citation.py` | The citation form California courts use. |
| `us/ca/counties/sacramento/` | Sacramento County. |
| `us/ca/counties/sacramento/cities/sacramento.py` | The City of Sacramento. |
| `us/ca/counties/sacramento/zoning.py` | The County's Zoning Code, from the County's own pages: `fetch` saves the chapters, `SacramentoZoningCode` yields the sections. |
| `us/states/<state>.py` | Another US state, one module, until it has a publication of its own; then it is a package like `us/ca/`. |
| `apa.py`, `caml.py`, `california.py` | Names that stay in the root only so an import that has not moved still works; each is the module under `us/ca/`. |
| `jurisdiction.py` | Country, region, state, county, and city. |
| `publication.py` | One file layout: statute, measure, or regulation. |
| `indexer.py` | The local Whoosh index. |
| `ledger.py` | Word counts per place, built in parallel once per index generation. A scope is a sum over places; see [tree.md](tree.md). |
| `query.py` | The structured lookup Jason calls. How a code's headings nest, and how a node is addressed, is [tree.md](tree.md). |
| `mcp_server.py` | The agent tools over that index. |
| `history.py` | One section, or a span, edition by edition on the shelf: the history note read, and what changed. See [history.md](history.md). |
| `succession.py` | Which section continues a former one: the Law Revision Commission's disposition tables and Comments (saved in `data/clrc`), and similarity candidates. See [history.md](history.md). |

A future country is a sibling of `us/`, named with its ISO 3166-1 alpha-2 in lowercase (`gb/`, `ca/` for Canada). The branch for the United States is `US`. `main` and `master` point at the same commit.

## Governments

`pycountry` is the catalog of codes. A class stores only its own code.

| Class | Code | Example |
| --- | --- | --- |
| `Country` | ISO 3166-1 alpha-2 | `US` |
| `Region` | ISO 3166-2 | `US-CA`, `JP-13` |
| `State` | A US region whose type is State | `US-CA` |
| `County` | Not an ISO code. Parent is the state. | Sacramento County, parent `US-CA` |
| `City` | Not an ISO code. In the US, parent is a county. | City of Sacramento |

`Country.layers` is the order under a region. For the United States it is county, then city. Another country can use a different order, or none. A Japanese prefecture is a region. It does not get a second statute corpus just because it has an ISO code.

`legislates` on a region is false when that region does not publish statutes.

## Local codes

A local government's code is a `Codification` on its `Locality` (`codes`): the title, the `Host` that serves it, the government's own page (`pointer`), its own edition of the words (`text`) when it keeps one, and where the ordinances are. `Host` is a closed set: `OFFICIAL`, and the commercial codifiers (`AMERICAN_LEGAL`, `GENERAL_CODE`, `MUNICODE`, `QUALITY_CODE`), which are never sources. A codification is `readable` only when the government publishes it itself. Sacramento: the City Code (Quality Code Publishing, served by American Legal) and the County Code (General Code, eCode360) are pointers; the County's Zoning Code is published by the County at landuse.saccounty.gov and has a parser. `query.place` lists them, and an ordinance citation is a miss that carries them.

## Publications

The thing being indexed is the plain text of a section. `LEGAL_TEXT` is those words. An edition is added when a government file yields the words. Prefer plain text or Word. Prefer an XML-like file (XML, SGML, CAML) over HTML or PDF of the same code. A distribution that is only PDF or HTML stays `editions = ()` until the words can be recovered from it.

An edition subclass implements `accepts` and `sections`. `accepts` is how a new year's files get their own parser without disturbing the current one.

California has two editions:

- `CaliforniaCodes` reads the code tables. Those tables are in the odd-year session zip from 2011 on. `pubinfo_2025.zip` is still the current session through 2026. Daily zips do not contain the codes.
- `CaliforniaBills` reads measures in zips that have `BILL_VERSION_TBL` and no `LAW_SECTION_TBL` (1989 through 2009).

`LAW_CODE` is the code of law (`CIV`, `PEN`). It is not the jurisdiction. The jurisdiction is `SUBDIVISION` (`US-CA`).

Who is authorized to publish each of those files, and which statute created the agency that adopted the rules, is [special/authority.md](special/authority.md). The official publication URLs and each state’s agency directory are indexed in [special/index.md](special/index.md).

## Corpora

Each publishing subdivision gets its own SQLite file and the same `section` table. A query opens an in-memory connection and `ATTACH DATABASE`s only the files it names. The schema name is the subdivision: `us` for the United States Code, `us_ca` for California, `cfr_24` for that CFR title, `us_ca_civ` for the Civil Code if that code is stored as its own file. A missing file is left detached. The attached schemas share no tables with each other, so a read is `us_ca.section` or a union across the schemas the query attached.

| Place | File |
| --- | --- |
| United States Code | `data/codes/US.sqlite` |
| California codes, current publication | `data/codes/US-CA.sqlite` |
| An older California session | `data/codes/US-CA/sessions/2009.sqlite` |
| Sacramento County | `data/codes/US-CA/sacramento.sqlite` |
| City of Sacramento | `data/codes/US-CA/sacramento/sacramento.sqlite` |
| One CFR title | `data/codes/US/cfr/24.sqlite`, schema `cfr_24` |
| One official manual | `data/codes/US/manuals/OLRC.sqlite`, schema `manual_olrc` |
| One California code, when split out | `data/codes/US-CA/statutes/CIV.sqlite`, schema `us_ca_civ` |

A canton or other region uses the same rule as a state: one file named with its ISO 3166-2 code. `data/idx` is the Whoosh index already built for California. New corpora are the SQLite files above.

## What is not a source

Commercial hosts are not crawled: Justia, FindLaw, Westlaw, Lexis, Fastcase, Municode, American Legal, General Code. Arkansas, Georgia, Mississippi, and Tennessee send the public code to Lexis. Those states stay empty.

County ordinances are one county at a time. See [counties.md](counties.md). There is no state-hosted bulk of them. A Sacramento ordinance query is a miss. The state code is still searchable.

## Adding a place

1. Subclass the layer that matches the government (`State`, `County`, `City`).
2. Set `code` or `parent` to a value `pycountry` already knows, or to the locality outside it.
3. Point `source` at the official file closest to plain text. An XML-like file outranks HTML and PDF of the same code.
4. Add an edition when that file yields the words. A PDF or HTML-only publication stays `editions = ()`.
5. Put the module where the parent lives: `us/ca/counties/<county>/` and `cities/` under that county.

`Idaho.counties()` is an empty dict until a county module exists. `California.counties()['sacramento']` is Sacramento County. `SacramentoCounty.cities()['sacramento']` is the city.
