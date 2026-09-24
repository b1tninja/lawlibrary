# lawlibrary

Catalog of the California codes, built only from the Legislature's own publications at <https://downloads.leginfo.legislature.ca.gov/>.

Aaron Swartz's html2text turns each section's CAML into plain text. Whoosh indexes that text. An MCP server answers an agent from the local index: search, open a section, list the codes.

`Publication` is the parser for one file layout. `California` is the distribution point (`downloads.leginfo.legislature.ca.gov`) and chooses an edition by the tables inside the zip. `CaliforniaCodes` is the code tables, published in the session zips from 2011 on. `CaliforniaBills` is the earlier sessions, which carry measures and no code tables. A later change in column layout is another subclass with its own `accepts`.

The current session is the odd-year file (`pubinfo_2025.zip` through 2026). It is refreshed weekly and is the file that contains the codes. Daily zips do not.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Use

```bash
python ca.py --download          # every pubinfo_YYYY.zip
python ca.py --index             # parse CAML in a process pool, write Whoosh here
python ca.py --current --index   # newest session only
python ca.py --get CIV 1940
python ca.py -q "habitability"
lawlibrary-mcp                   # list_codes, list_sessions, search_law, get_section
```

Search and `get_section` use the newest session unless you pass an older year or `all`. Historical zips are frozen; the current session is the law in force.

CAML parsing is the slow part, so index workers each open the zip and run html2text. The Whoosh writer stays in the parent process. `--workers` sets the pool size.

`data/` holds the zips and the index. It is not committed.

## Official distribution points

Each state is a `State` subclass. The URL is the government host only. Notes, file shapes, and the commercial hosts we do not crawl are in [docs/state-publications.md](docs/state-publications.md). One git branch per state, `state/<name>`, tracks `origin`.

| State | Official distribution |
| --- | --- |
| Alabama | <https://alison.legislature.state.al.us/code-of-alabama> |
| Alaska | <https://www.akleg.gov/statutesPDF/Title-1.pdf> (per title) |
| Arizona | <https://www.azleg.gov/ARStitle/> |
| Arkansas | <https://www.arkleg.state.ar.us/ArkansasLaw> (public code is Lexis; no government file) |
| California | <https://downloads.leginfo.legislature.ca.gov/> |
| Colorado | <https://olls.info/crs/crs2026-htm.zip> |
| Connecticut | <https://prdext2.cga.ct.gov/current/pub/titles.htm> |
| Delaware | <https://delcode.delaware.gov/> |
| Florida | <https://www.leg.state.fl.us/Statutes/FLLawDL2026.zip> |
| Georgia | <https://www.lexisnexis.com/hottopics/gacode/> is the legislature's link (no government file) |
| Hawaii | <https://data.capitol.hawaii.gov/hrscurrent/> |
| Idaho | <https://legislature.idaho.gov/statutesrules/idstat/> |
| Illinois | <https://www.ilga.gov/ftp/ILCS/> |
| Indiana | <https://iga.in.gov/laws/ic/downloads> |
| Iowa | <https://www.legis.iowa.gov/law/iowaCode?year=2026> |
| Kansas | <https://www.kslegislature.gov/b2025_26/laws/> |
| Kentucky | <https://apps.legislature.ky.gov/law/statutes/> |
| Louisiana | <https://legis.la.gov/legis/LawsContents.aspx> |
| Maine | <https://legislature.maine.gov/legis/statutes/homepage.html> |
| Maryland | <https://mgaleg.maryland.gov/mgawebsite/laws/statutes> |
| Massachusetts | <https://malegislature.gov/Laws/GeneralLaws/> |
| Michigan | <https://www.legislature.mi.gov/documents/mcl/> |
| Minnesota | <https://www.revisor.mn.gov/statutes/> |
| Mississippi | Legislature links the code to Lexis; no government file |
| Missouri | <https://revisor.mo.gov/> |
| Montana | <https://mca.legmt.gov/bills/mca/> |
| Nebraska | <https://github.com/nelegislature/LegalDocs> |
| Nevada | <https://www.leg.state.nv.us/nrs/> |
| New Hampshire | <https://gc.nh.gov/rsa/html/NHTOC.HTM> |
| New Jersey | <https://pub.njleg.gov/statutes/STATUTES-TEXT.zip> |
| New Mexico | <https://nmonesource.com/> |
| New York | <https://legislation.nysenate.gov/api/3/laws> |
| North Carolina | <https://www.ncleg.gov/Laws/GeneralStatutesTOC> |
| North Dakota | <https://ndlegis.gov/api/data/century_code.json> |
| Ohio | <https://codes.ohio.gov/ohio-revised-code> |
| Oklahoma | <https://www.oklegislature.gov/osStatuesTitle.html> |
| Oregon | <https://www.oregonlegislature.gov/bills_laws/pages/ors.aspx> |
| Pennsylvania | <https://www.palegis.us/statutes/consolidated> |
| Rhode Island | <https://webserver.rilegislature.gov/statutes/Statutes.html> |
| South Carolina | <https://www.scstatehouse.gov/code/statmast.php> |
| South Dakota | <https://sdlegislature.gov/Statutes> |
| Tennessee | Code Bill PDFs at <https://www.capitol.tn.gov/legislation/publications/index.html> (not the whole code; the code link is Lexis) |
| Texas | <https://statutes.capitol.texas.gov/download> |
| Utah | <https://glen.le.utah.gov/code/> |
| Vermont | <https://legislature.vermont.gov/statutes> |
| Virginia | <https://law.lis.virginia.gov/law-library/> |
| Washington | <https://lawfilesext.leg.wa.gov/Law/RCWArchive/2025/pdf/> |
| West Virginia | <https://code.wvlegislature.gov/> |
| Wisconsin | <https://docs.legis.wisconsin.gov/statutes/statutes/> |
| Wyoming | <https://wyoleg.gov/statutes/compress/> |
