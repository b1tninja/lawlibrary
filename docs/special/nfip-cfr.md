# National Flood Insurance Program (statute, CFR, Federal Register)

How lawlibrary can fetch the **words** of the National Flood Insurance Program from official government hosts only. The index stores plain text. Prefer an XML-like file over HTML or PDF of the same code. Commercial hosts are not sources. Do not invent regulatory quotes; quote only text recovered from a fetched official file.

Checked 2026-09-24 by reading House OLRC, GPO govinfo, eCFR API, and NARA/OFR pages (HEAD or GET where noted). Large XML belongs under `data/`, not in git.

FEMA administers the program under the Homeland Security Act, 6 U.S.C. § 313, and the National Flood Insurance Act, 42 U.S.C. § 4001 et seq. The regulations are published by the Office of the Federal Register in the Code of Federal Regulations, 44 U.S.C. § 1510, not by FEMA as a separate code. See [authority.md](authority.md).

## What to fetch

| Layer | What it is | Preferred machine-readable file | Legal edition (not the parse format) |
| --- | --- | --- | --- |
| Statute | 42 U.S.C. chapter 50 (National Flood Insurance), from § 4001 | Same Title 42 USLM XML zip as Fair Housing / ADA | OLRC United States Code (USLM/XML from [uscode.house.gov/download](https://uscode.house.gov/download/download.shtml)) |
| Compiled regulations | 44 CFR chapter I, subchapter B (Insurance and Hazard Mitigation), especially parts 59–80 | eCFR Title 44 XML (bulk or versioner API) | Annual CFR PDF and Text on govinfo (titles 42–50 revised as of October 1) |
| Daily amendments | Federal Register rule text that amends the CFR | Per-issue or bulk FR XML on govinfo | Digitally signed FR PDF (and Text) on govinfo; XML is not the official online format |

A parser should **start with Title 44 eCFR XML** for NFIP regulation words. Use the annual CFR PDF/Text only to name the legal edition or to verify against it—not as the preferred ingest format. Use Federal Register XML for daily amendment words; do not crawl federalregister.gov HTML as the corpus.

## Statute: 42 U.S.C. chapter 50

The National Flood Insurance Act material lives in **Title 42** of the United States Code (The Public Health and Welfare), **chapter 50** (National Flood Insurance), beginning at **section 4001**.

That text is in the **same Title 42 USLM XML file** used for Fair Housing and the ADA. Fetch design, release-point URLs, and corpus placement for the Code are documented in [us-code.md](us-code.md). **Do not duplicate a full US Code download design here.** For NFIP statute sections, load Title 42 once and select chapter 50 / § 4001 et seq. from that file.

As of this check, the OLRC current-release download page listed Title 42 XML among the title downloads, current through Public Law 119-111 (09/18/2026). Example title zip (HEAD 200): `https://uscode.house.gov/download/releasepoints/us/pl/119/111/xml_usc42@119-111.zip`. Prefer the links on the download page for the live release point; the path embeds the public-law number and changes when OLRC publishes a new point.

Browse (HTML, not the corpus): chapter 50 prelim view returns HTML from `uscode.house.gov` (HEAD 200 on the granule browse URL).

## Regulations: 44 CFR chapter I, subchapter B

Title 44 is **Emergency Management and Assistance**. FEMA’s chapter I includes **Subchapter B—Insurance and Hazard Mitigation**. The eCFR structure API for a dated title lists that subchapter and its parts (confirmed via `https://www.ecfr.gov/api/versioner/v1/structure/2026-06-24/title-44.json`). Parts **59–80** are the main NFIP block (general provisions, land-use criteria, insurance, mapping, appeals, mitigation grants, open-space acquisition, and reserved placeholders). Parts 50–58 and many numbers after 80 are reserved or outside that NFIP core.

### Bulk eCFR XML (govinfo)

Directory (verified listing): <https://www.govinfo.gov/bulkdata/ECFR/title-44>

| File | Notes (as listed) |
| --- | --- |
| `ECFR-title44.xml` | Full Title 44 eCFR XML (~2.3 MB on this check; last modified 24-Jun-2026) |
| `ECFR-title44-graphics.zip` | Graphics companion |

Direct file (HEAD 200, `text/xml`): `https://www.govinfo.gov/bulkdata/ECFR/title-44/ECFR-title44.xml`

Parent tree: <https://www.govinfo.gov/bulkdata/ECFR>

Schema / user guide: under `https://www.govinfo.gov/bulkdata/ECFR/resources/` (includes `ECFR-XML-User-Guide.pdf`).

### eCFR versioner API (still live)

Titles index (GET JSON, verified): `https://www.ecfr.gov/api/versioner/v1/titles.json` — Title 44 appears as “Emergency Management and Assistance” with `up_to_date_as_of` and amendment dates.

Full title XML path (confirmed HEAD 200, `application/xml`):

`https://www.ecfr.gov/api/versioner/v1/full/{date}/title-44.xml`

Example used for this check: `https://www.ecfr.gov/api/versioner/v1/full/2026-06-24/title-44.xml`. Choose `{date}` from the titles / versions API so the snapshot matches a real eCFR date; Title 44’s latest amendment on the titles payload was 2026-06-22 as of this check.

Structure without downloading the full title: `https://www.ecfr.gov/api/versioner/v1/structure/{date}/title-44.json`.

eCFR HTML browse may challenge automated clients; use the **API and govinfo bulk XML**, not a site scrape.

### Legal status of eCFR XML (not the official CFR)

GPO / OFR state plainly that the **eCFR is not an official legal edition of the CFR**. The eCFR (and its XML bulk) is an editorial compilation of CFR material and Federal Register amendments, updated daily. See:

- <https://www.ecfr.gov/> (banner: eCFR is not an official legal edition)
- <https://www.archives.gov/federal-register/cfr/about-ecfr>
- <https://www.govinfo.gov/help/cfr>
- ECFR XML User Guide FAQ: bulk eCFR XML is **not** part of the official online format of the CFR; **PDF and Text** of the annual CFR on govinfo (formerly FDsys) **have legal status** as parts of that official online format. eCFR XML files are **not** digitally signed.

### Edition that does have legal status

The **annual editions of the CFR** on govinfo—**PDF** (and ASCII **Text**)—are the official editions sanctioned by the Administrative Committee of the Federal Register (see NARA: <https://www.archives.gov/federal-register/cfr/about.html>, 1 CFR part 8). Titles **42–50** are revised as of **October 1**.

Example annual Title 44 volume (HEAD 200 PDF):  
`https://www.govinfo.gov/content/pkg/CFR-2025-title44-vol1/pdf/CFR-2025-title44-vol1.pdf`

Annual bulk XML also exists (useful words, still not the preferred “legal edition” claim):  
<https://www.govinfo.gov/bulkdata/CFR/2025/title-44> lists `CFR-2025-title44-vol1.xml` and `CFR-2025-title-44.zip`. Treat that XML like other bulk CFR XML: machine-readable, not a substitute for naming the official PDF/Text edition.

**Do not prefer PDF as the parse format.** Rank: eCFR / annual CFR **XML** for section words; keep annual PDF/Text as the named legal edition and verification target.

## Federal Register: daily amendment source

The Federal Register is the **daily** publication of rules (and proposed rules, notices). It is the amendment stream that the eCFR and the next annual CFR absorb. It is **not** the compiled code.

### Bulk and per-issue XML (govinfo)

- Bulk root (verified): <https://www.govinfo.gov/bulkdata/FR>
- By year (verified 2026 listing): <https://www.govinfo.gov/bulkdata/FR/2026> (monthly folders plus year zip)
- Per-issue XML pattern (govinfo sample URLs; HEAD 200 on a recent issue):  
  `https://www.govinfo.gov/content/pkg/FR-{YYYY-MM-DD}/xml/FR-{YYYY-MM-DD}.xml`  
  Example: `https://www.govinfo.gov/content/pkg/FR-2026-09-23/xml/FR-2026-09-23.xml`

Matching signed PDF for the same issue:  
`https://www.govinfo.gov/content/pkg/FR-{YYYY-MM-DD}/pdf/FR-{YYYY-MM-DD}.pdf`

Help / URL patterns: <https://www.govinfo.gov/help/fr>

### Legal status of FR XML

The online Federal Register on govinfo is the official legal equivalent of paper/microfiche (44 U.S.C. 4101; 1 CFR 5.10)—but the **FR XML User Guide** states that **XML bulk files are not part of the official online format**. Only the **PDF and Text** versions have legal status as parts of that official online format. XML downloads are **not** digitally signed; GPO applies digital signatures to the **PDF** documents (Seal of Authenticity).

A parser uses **FR XML for words**. It does **not** crawl **federalregister.gov** HTML as the corpus (that site is an OFR HTML edition / public-inspection front end, not the govinfo signed package set).

## Corpus placement

NFIP regulations are a **CFR title publication**, not a row inside `data/codes/US-CA.sqlite` (California statutes) and not a substitute for the United States Code file `data/codes/US.sqlite`.

**Suggested path:** `data/codes/US-CFR-44.sqlite`

Why title-scoped rather than one country-level `US-CFR.sqlite`:

- Layout already maps **one complete published code** to one SQLite file (`docs/layout.md`). Title 44 is one GPO/eCFR title download; other titles are other publications.
- `US.sqlite` is reserved for the **United States Code** (statutes). Mixing all 50 CFR titles into one file would blur statute vs regulation and force unrelated agency rules into every NFIP open.
- A later all-titles regulations corpus can still be named deliberately; for NFIP ingest, **Title 44 alone** matches the fetch unit (`ECFR-title44.xml` / `title-44.xml`).

Statute sections from chapter 50 belong in the **US Code** corpus described in [us-code.md](us-code.md), not in the CFR file. Federal Register issues, if indexed at all, are a separate daily publication—not folded into `US-CA.sqlite`.

**Do not invent a new Python code class** for this note. Document the file path and sources; wire a class only when an edition parser is added.

## What is not a source

Justia, FindLaw, Westlaw, Lexis, Fastcase, Cornell LII mirrors when used instead of OLRC/govinfo/eCFR, FEMA brochure HTML when used instead of the CFR/FR text, and federalregister.gov HTML scrapes as the primary corpus.

## Short summary

| Need | Fetchable XML | Legal edition | Parser start? |
| --- | --- | --- | --- |
| Statute (42 U.S.C. ch. 50) | Title 42 USLM (same file as Fair Housing / ADA) | OLRC US Code release | With the US Code Title 42 ingest—not a second download design |
| Compiled NFIP regs (44 CFR) | **Yes:** `ECFR-title44.xml` and `…/full/{date}/title-44.xml` | **Annual CFR PDF/Text** on govinfo (eCFR XML is **not** official) | **Yes—start here** for regulation words |
| Daily amendments | **Yes:** govinfo `FR` bulk and `FR-{date}.xml` | **Signed FR PDF** (and Text); FR XML is not the official format | FR XML for amendment words only; not federalregister.gov HTML |
