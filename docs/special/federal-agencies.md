# Federal agencies and CFR titles (community-association management)

Which federal departments publish the **regulations** a California community-association manager commonly hits, and how those map onto the Code of Federal Regulations for fetch design. Checked 2026-09-24 against GPO govinfo bulk ECFR directories (HEAD and directory listings) and the eCFR versioner structure API. Official hosts only. Commercial hosts are not sources. Do not invent regulatory quotes; quote only text recovered from a fetched official file.

Who created each department, and which statute lets it adopt the rules below, is in [authority.md](authority.md). This note is about the **CFR** (agency regulations). Fair Housing and ADA **statutes** live in the United States Code and are documented in [us-code.md](us-code.md). NFIP statute / Title 44 / Federal Register fetch design is documented in [nfip-cfr.md](nfip-cfr.md)—do not duplicate that design here. California **CCR** Title 24 (Building Standards Code) is a different code; see [title-24.md](title-24.md). That state Title 24 is not HUD’s **24 CFR**.

## Index unit

The index unit for regulations is **one complete CFR title** as govinfo bulk eCFR XML:

`https://www.govinfo.gov/bulkdata/ECFR/title-N/ECFR-titleN.xml`

Example: Title 24 → `https://www.govinfo.gov/bulkdata/ECFR/title-24/ECFR-title24.xml`.

Do **not** scrape each agency’s HTML brochure, fact sheet, or guidance page as the corpus. Agency sites below are **pointers** to the right title and parts. Prefer XML over HTML or PDF of the same code. Large XML belongs under `data/`, not in git. `us/cfr` parses one title XML file into `data/codes/US/cfr/{title}.sqlite`. See [cfr.md](cfr.md).

Parent tree: <https://www.govinfo.gov/bulkdata/ECFR>  
Schema / user guide: under `https://www.govinfo.gov/bulkdata/ECFR/resources/`

Alternate live snapshot (still eCFR, still not the official annual CFR edition):  
`https://www.ecfr.gov/api/versioner/v1/full/{date}/title-N.xml`  
Choose `{date}` from `https://www.ecfr.gov/api/versioner/v1/titles.json`. Structure without the full file: `…/structure/{date}/title-N.json`.

### Legal status (same ranking as nfip-cfr.md)

GPO / OFR state that the **eCFR is not an official legal edition of the CFR**. Bulk eCFR XML is machine-readable compilation text. The **annual CFR PDF and Text** on govinfo have legal status as parts of the official online format. Rank: **XML for section words**; keep annual PDF/Text as the named legal edition when claiming one. See <https://www.ecfr.gov/>, <https://www.archives.gov/federal-register/cfr/about-ecfr>, and <https://www.govinfo.gov/help/cfr>.

## Agencies and CFR parts

Part labels below come from the eCFR structure API for dated titles (check date 2026-09-23 on the titles index). No regulatory body text is pasted here.

### HUD — Department of Housing and Urban Development

| | |
| --- | --- |
| **Department** | Housing and Urban Development |
| **CFR title** | **24** — Housing and Urban Development |
| **Bulk XML** | `https://www.govinfo.gov/bulkdata/ECFR/title-24/ECFR-title24.xml` |
| **Directory** | <https://www.govinfo.gov/bulkdata/ECFR/title-24> (listed `ECFR-title24.xml`; HEAD 200 on directory and XML) |

**Parts that matter for association management**

| Part | Why it shows up |
| --- | --- |
| **100** | Discriminatory Conduct Under the Fair Housing Act (HUD’s FHA regulations: sales/rentals, disability accommodations/modifications, familial status, advertising, and related rules). Statute is **42 U.S.C. chapter 45**—fetch that from the US Code file in [us-code.md](us-code.md), not from this title. |
| **103**, **110**, **115**, **121**, **180** | Complaint processing, fair housing poster, state/local agency certification, data collection, consolidated civil-rights hearing procedures (enforcement/process around Part 100). |
| **35** | Lead-Based Paint Poisoning Prevention in Certain Residential Structures (HUD rules). **Subpart A** is disclosure on sale/lease of most pre-1978 housing; **subparts B–R** are the Lead Safe Housing Rule stack for federally owned/assisted housing. Private HOA/condo sales and leases commonly hit disclosure; assisted-housing subparts apply when federal assistance is in play. |

Agency pointer (not the corpus): HUD Fair Housing / FHEO materials on [hud.gov](https://www.hud.gov/). Part browse on eCFR (HTML, not ingest): [24 CFR Part 100](https://www.ecfr.gov/current/title-24/part-100), [24 CFR Part 35](https://www.ecfr.gov/current/title-24/part-35).

**Joint lead rules:** EPA’s renovation and (parallel) disclosure text is in **40 CFR Part 745** (below). HUD’s companion disclosure and federally assisted lead rules stay in **24 CFR Part 35**. Same topic family; two titles; one Title 24 XML file covers the HUD side.

### DOJ — Department of Justice

| | |
| --- | --- |
| **Department** | Justice |
| **CFR title** | **28** — Judicial Administration |
| **Bulk XML** | `https://www.govinfo.gov/bulkdata/ECFR/title-28/ECFR-title28.xml` |
| **Directory** | <https://www.govinfo.gov/bulkdata/ECFR/title-28> (listed `ECFR-title28.xml`; HEAD 200 on directory and XML) |

| Part | Why it shows up |
| --- | --- |
| **35** | ADA **Title II** — nondiscrimination on the basis of disability in state and local government services (28 CFR chapter I). |
| **36** | ADA **Title III** — nondiscrimination on the basis of disability by public accommodations and in commercial facilities. Clubhouses, pools, and other facilities open to the public as public accommodations are the usual association touchpoint; applicability is fact-specific. |

ADA **statute** is **42 U.S.C. chapter 126** ([us-code.md](us-code.md)). These parts are the Attorney General’s implementing regulations, not a second copy of the Code.

Agency pointers: [ADA.gov Title II regulations](https://www.ada.gov/law-and-regs/regulations/title-ii-2010-regulations/), [Title III regulations](https://www.ada.gov/law-and-regs/regulations/title-iii-regulations/). eCFR browse: [28 CFR Part 35](https://www.ecfr.gov/current/title-28/part-35), [Part 36](https://www.ecfr.gov/current/title-28/part-36).

### FEMA — Department of Homeland Security (Federal Emergency Management Agency)

| | |
| --- | --- |
| **Department** | Homeland Security (FEMA) |
| **CFR title** | **44** — Emergency Management and Assistance |
| **Bulk XML** | `https://www.govinfo.gov/bulkdata/ECFR/title-44/ECFR-title44.xml` |
| **Directory** | <https://www.govinfo.gov/bulkdata/ECFR/title-44> (listed `ECFR-title44.xml`; HEAD 200 on directory and XML) |

NFIP compiled regulations sit in Title 44 chapter I, subchapter B, especially **parts 59–80**. Full fetch design (eCFR vs annual CFR, FR amendments, suggested `data/codes/US-CFR-44.sqlite`) is in **[nfip-cfr.md](nfip-cfr.md)**. Do not repeat that design here; point parsers at that note for Title 44.

### FCC — Federal Communications Commission

| | |
| --- | --- |
| **Agency** | Federal Communications Commission (independent) |
| **CFR title** | **47** — Telecommunication |
| **Bulk XML** | `https://www.govinfo.gov/bulkdata/ECFR/title-47/ECFR-title47.xml` |
| **Directory** | <https://www.govinfo.gov/bulkdata/ECFR/title-47> (listed `ECFR-title47.xml`; HEAD 200 on directory and XML) |

| Location | Why it shows up |
| --- | --- |
| **Part 1**, **§ 1.4000** (subpart S) | Over-the-Air Reception Devices (**OTARD**) rule—restrictions (including private covenant / association rules) that impair covered video and certain fixed-wireless antennas on property within the user’s exclusive use or control. Confirmed in eCFR structure as section `1.4000` under part 1. |

Agency pointer: [FCC OTARD rule page](https://www.fcc.gov/media/over-air-reception-devices-rule) (cites 47 C.F.R. § 1.4000). The ingest file is still the **whole Title 47** XML, not that HTML page. Part 25 (Satellite Communications) is related spectrum/service material; OTARD text for association disputes is the Part 1 section above.

### EPA — Environmental Protection Agency

| | |
| --- | --- |
| **Agency** | Environmental Protection Agency (independent) |
| **CFR title** | **40** — Protection of Environment |
| **Bulk XML** | `https://www.govinfo.gov/bulkdata/ECFR/title-40/ECFR-title40.xml` |
| **Directory** | <https://www.govinfo.gov/bulkdata/ECFR/title-40> (listed `ECFR-title40.xml`; HEAD 200 on directory and XML; large file) |

| Part | Why it shows up |
| --- | --- |
| **745** | Lead-Based Paint Poisoning Prevention in Certain Residential Structures (Toxic Substances Control Act chapter). **Subpart E** — residential property renovation (RRP). **Subpart F** — disclosure (EPA side of the sale/lease disclosure regime). **Subpart L** — lead-based paint activities (abatement, etc.). |

Agency pointer: [EPA Lead RRP rules](https://www.epa.gov/lead/lead-renovation-repair-and-painting-program-rules) (points at 40 CFR Part 745, Subpart E). HUD joint / parallel rules remain in **24 CFR Part 35** (above)—fetch Title 24 for HUD text and Title 40 for EPA text; do not treat an EPA HTML guide as either title.

### OSHA / Labor — Department of Labor

| | |
| --- | --- |
| **Department** | Labor (Occupational Safety and Health Administration) |
| **CFR title** | **29** — Labor |
| **Bulk XML** | `https://www.govinfo.gov/bulkdata/ECFR/title-29/ECFR-title29.xml` |
| **Directory** | <https://www.govinfo.gov/bulkdata/ECFR/title-29> (listed `ECFR-title29.xml`; HEAD 200 on directory and XML) |

Official title XML **exists**, so Labor is in scope for a title-level fetch. Chapter XVII holds OSHA standards. Parts that matter when an association or its contractors employ workers on site:

| Part | Label (structure API) |
| --- | --- |
| **1903** | Inspections, Citations and Proposed Penalties |
| **1904** | Recording and Reporting Occupational Injuries and Illnesses |
| **1910** | Occupational Safety and Health Standards (general industry) |
| **1926** | Safety and Health Regulations for Construction |

Many day-to-day association duties never reach these parts; they are listed because maintenance, renovation, and contractor oversight can. The fetch unit remains **Title 29** as a whole, not a brochure scrape from osha.gov.

## Federal Register (amendments, not a second CFR)

The **Federal Register** is the **daily** publication of rules (and proposed rules, notices). It is the amendment stream that the eCFR and the next annual CFR absorb. It is **not** a second compiled copy of the CFR and must not be indexed as if it were Title *N*.

Bulk / per-issue XML on govinfo, legal-status ranking (FR XML for words; signed PDF/Text for official online format), and the warning against crawling federalregister.gov HTML as the corpus are already covered in [nfip-cfr.md](nfip-cfr.md). Reuse that pattern for any title’s amendments.

## What is not a source

Westlaw, Lexis, Justia, FindLaw, Fastcase, Cornell LII mirrors used instead of govinfo / eCFR / agency.gov pointers; agency HTML brochures used instead of title XML; federalregister.gov HTML scrapes as the primary corpus; invented quotes from part numbers alone.

## Verification table (2026-09-24)

| Agency / department | CFR title | Bulk directory URL | Directory / XML responded |
| --- | --- | --- | --- |
| HUD | 24 | <https://www.govinfo.gov/bulkdata/ECFR/title-24> | Yes (HEAD 200; listing shows `ECFR-title24.xml`) |
| DOJ | 28 | <https://www.govinfo.gov/bulkdata/ECFR/title-28> | Yes (HEAD 200; listing shows `ECFR-title28.xml`) |
| DOL / OSHA | 29 | <https://www.govinfo.gov/bulkdata/ECFR/title-29> | Yes (HEAD 200; listing shows `ECFR-title29.xml`) |
| EPA | 40 | <https://www.govinfo.gov/bulkdata/ECFR/title-40> | Yes (HEAD 200; listing shows `ECFR-title40.xml`) |
| FEMA | 44 | <https://www.govinfo.gov/bulkdata/ECFR/title-44> | Yes (HEAD 200; listing shows `ECFR-title44.xml`) — details in [nfip-cfr.md](nfip-cfr.md) |
| FCC | 47 | <https://www.govinfo.gov/bulkdata/ECFR/title-47> | Yes (HEAD 200; listing shows `ECFR-title47.xml`) |

URL pattern for each title file: `https://www.govinfo.gov/bulkdata/ECFR/title-N/ECFR-titleN.xml`.

## Short summary

| Need | Where |
| --- | --- |
| Index / fetch unit | One complete **CFR title** eCFR XML on govinfo bulkdata (not per-agency HTML) |
| FHA / ADA **statutes** | [us-code.md](us-code.md) (Title 42 USLM) |
| FHA **regulations** | 24 CFR (esp. Part 100); Title 24 XML |
| ADA Title II / III **regulations** | 28 CFR Parts 35–36; Title 28 XML |
| NFIP **regulations** | 44 CFR; see [nfip-cfr.md](nfip-cfr.md) |
| OTARD | 47 CFR § 1.4000 inside Title 47 XML |
| Lead (EPA + HUD) | 40 CFR Part 745 and 24 CFR Part 35 |
| OSHA (if needed) | 29 CFR chapter XVII; Title 29 XML exists |
| Daily amendments | Federal Register XML on govinfo — not a second compiled CFR |
