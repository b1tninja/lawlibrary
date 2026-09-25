# California agency regulations (outside statute zips)

Survey of departments that publish, or point to, **regulations** outside the Legislature’s pubinfo statute zips. Checked 2026-09-24 by reading official agency pages. The index stores plain text. XML-like files outrank HTML and PDF. Commercial hosts are not crawled. Do not invent regulation text. Do not crawl `govt.westlaw.com` or Barclays. Do not commit PDFs into git.

The Office of Administrative Law publishes the California Code of Regulations because Government Code § 11344 says it must. Each department below adopts rules under the Administrative Procedure Act and the statute that created that department. Those statutes are in [authority.md](authority.md).

Business and Professions Code (and other California codes) already come from Legislative Counsel **pubinfo**. Do **not** re-parse those statutes from an agency PDF or HTML reprint.

The complete list of departments, boards, and commissions is the Secretary of State’s California Roster, section “State Agencies, Departments, Boards, and Commissions,” linked from [sos.ca.gov/administration/california-roster](https://www.sos.ca.gov/administration/california-roster/). The rows below are the ones already opened. Letter ranges of the roster are recorded under `ca-roster/` as they are checked.

## Verdict

**No indexer.** Across the agencies below, no official bulk **XML** or **plain-text** (or Word) file of compiled regulations was found on a government host this project will crawl. What exists is:

- OAL’s Official CCR on Barclays/Westlaw (not a source)
- Department PDF compilations and rulemaking express-terms PDFs
- Occasional HTML section pages (still HTML, not an edition shape for a new parser)
- Copyrighted model-code viewers for Title 24 Parts 2 and 9

A PDF URL list is not an edition. HTML pages are not an XML/text edition. **No package under `us/ca/regulations/`** until a government file yields the words in a preferred shape.

## Office of Administrative Law (CCR compilation)

| | |
| --- | --- |
| Host | [oal.ca.gov/publications/ccr/](https://oal.ca.gov/publications/ccr/) |
| Bulk XML / text | **None** |
| What they post | Link to the free online Official CCR under contract with Barclays (Thomson Reuters) at `govt.westlaw.com`; hard copy sold by Barclays; county clerks / law libraries / depository libraries hold print |
| Shape for this project | **Westlaw CCR only** — not a source |

OAL updates the official hard-copy and online CCR weekly. That page does not offer an OAL bulk XML, zip, FTP dump, or other government-hosted machine file of the CCR. The Notice Register is weekly **PDF** issues ([oal.ca.gov/california_regulatory_notice_online/](https://oal.ca.gov/california_regulatory_notice_online/)), not a regulation corpus.

## Department of Real Estate

See **[dre.md](dre.md)**. Title 10 CCR chapter 6 is the department’s Real Estate Law book **PDF** only (`regs.pdf`). Word/HTML/XML siblings 404. Edition stays empty. Do not re-parse B&P statutes from the DRE statute PDF.

## Building Standards Commission (Title 24)

See **[title-24.md](title-24.md)**. Parts 2 and 9 are copyrighted ICC publications (viewable online, not a government bulk download). Edition stays empty. Do not crawl ICC/NFPA/IAPMO viewers.

## Department of Housing and Community Development

| | |
| --- | --- |
| Host | [hcd.ca.gov](https://www.hcd.ca.gov/) — Title 25 rulemaking at [/building-standards/title-25-rulemaking](https://www.hcd.ca.gov/building-standards/title-25-rulemaking) |
| Bulk XML / text | **None** |
| What they post | Title 25 **rulemaking** packages and program regulation texts as **PDF** (e.g. Prohousing regulation text, State CDBG §§ 7050–7126). Program handbooks point readers to `oal.ca.gov` / Lexis for current Title 25 and to leginfo for statutes |
| Shape for this project | **PDF** (slip/rulemaking and program reprints) + **Westlaw CCR** for the compiled title |

HCD also develops Title 24 material; the adopted CBC/CFC words are not a segregable state bulk file (see title-24.md).

## Contractors State License Board

| | |
| --- | --- |
| Host | [cslb.ca.gov](https://www.cslb.ca.gov/) / [web.cslb.ca.gov](https://web.cslb.ca.gov/) — [Laws and Regulations](https://web.cslb.ca.gov/About_Us/Library/Laws/) |
| Bulk XML / text | **None** |
| What they post | Free **PDF** *California Contractors License Law & Reference Book* (2026: `…/GuidesAndPublications/2026/2026_CSLB_Law_Book.pdf`), which reprints Title 16 Division 8 extracted from Barclays Official CCR (Thomson/West copyright notice in the book). Per-action **PDF** final language on the Laws page |
| Shape for this project | **PDF** only (department book + rulemaking). Compiled CCR remains Westlaw |

CSLB’s public data/API endpoints are license lists (CSV/xlsx), not regulations.

## Department of Insurance

| | |
| --- | --- |
| Host | [insurance.ca.gov](https://www.insurance.ca.gov/) — [CCR index](https://www.insurance.ca.gov/01-consumers/130-laws-regs-hearings/05-CCR/index.cfm), [Regulations & Guidance](https://www.insurance.ca.gov/0250-insurers/0500-legal-info/0200-regulations/), [legaldocs.insurance.ca.gov](https://legaldocs.insurance.ca.gov/publicdocs/RegulationHome) |
| Bulk XML / text | **None** |
| What they post | Explicit statement that CDI “does not generally post its official regulations” on the site; readers are sent to the Official CCR (Title 10 Chapter 5). Rulemaking files and some consumer guides are **PDF**. Fair Claims pages list section titles; they are not a bulk XML/text dump of Title 10 |
| Shape for this project | **Westlaw CCR** for the compiled regs; **PDF** for rulemaking packages |

## Civil Rights Department (FEHA regulations)

| | |
| --- | --- |
| Host | [calcivilrights.ca.gov](https://calcivilrights.ca.gov/) — [Laws, Reports, and Statistics](https://calcivilrights.ca.gov/legalrecords/?content=law) |
| Bulk XML / text | **None** |
| What they post | FEHA / Title 2 Division 4.1 structure and article lists on **HTML** pages; statute links go to the Legislature. Rulemaking and tracked-change packages are **PDF** under `/wp-content/uploads/`. No Word/XML/txt compilation of the FEHA regulations was found |
| Shape for this project | **HTML** (browse) + **PDF** (rulemaking) + **Westlaw CCR** for the official compilation |

HTML article pages are not an XML/text edition.

## Office of the State Fire Marshal

| | |
| --- | --- |
| Host | [osfm.fire.ca.gov](https://osfm.fire.ca.gov/) — e.g. [Title 19 Development](https://osfm.fire.ca.gov/divisions/code-development-and-analysis/title-19-development/), [SFT regulations](https://osfm.fire.ca.gov/what-we-do/state-fire-training/regulations-and-incorporated-documents) |
| Bulk XML / text | **None** |
| What they post | Title 19 **rulemaking** express terms, notices, and manuals as **PDF** (and some HTML procedure manuals). Pipeline and training pages cite CCR Title 19 sections via external CCR links. Title 24 development is rulemaking history, not a bulk CBC/CFC file |
| Shape for this project | **PDF** (rulemaking) + **Westlaw CCR** for compiled Title 19 |

## California Coastal Commission

| | |
| --- | --- |
| Host | [coastal.ca.gov](https://www.coastal.ca.gov/) — [Laws](https://www.coastal.ca.gov/laws/), [Rulemaking](https://www.coastal.ca.gov/rulemaking/), older [leginfo/ccatc.html](https://www.coastal.ca.gov/leginfo/ccatc.html) |
| Bulk XML / text | **None** |
| What they post | Coastal Act chapter browse on the Commission site (statute material — already covered by pubinfo where it is Public Resources Code). Administrative regulations (Title 14 Division 5.5) are directed to the **Official CCR / Westlaw** tree. Rulemaking packages and statements of reasons are **PDF** on `documents.coastal.ca.gov` |
| Shape for this project | **Westlaw CCR** for Div. 5.5; **PDF** for rulemaking. Do not treat Coastal Act HTML as a second statute corpus |

## Other departments opened in this survey

| Agency | Host | Bulk XML / text | Notes |
| --- | --- | --- | --- |
| California Energy Commission | [energy.ca.gov](https://www.energy.ca.gov/rules-and-regulations) | **None** | Title 20 appliance / building standards rulemaking via efiling **PDF** express terms; no compiled Title 20 XML/text dump found |
| Department of Industrial Relations / DLSE | [dir.ca.gov](https://www.dir.ca.gov/dlse/CCR.htm), Title 8 HTML under `/t8/` | **None** (HTML only) | TOC and per-section **HTML** (e.g. `dir.ca.gov/t8/11701.html`). Also links “all Titles” to Westlaw CCR. HTML is not an XML/text edition |

## Corpus suggestion

| Publication | Preferred shape found | Indexer |
| --- | --- | --- |
| Official CCR (all APA titles) | Westlaw only | Do not add |
| DRE Title 10 ch. 6 | PDF | Empty — [dre.md](dre.md) |
| Title 24 Parts 2 & 9 | ICC copyright | Empty — [title-24.md](title-24.md) |
| HCD Title 25 | PDF + Westlaw | Do not add |
| CSLB Title 16 Div. 8 | PDF + Westlaw | Do not add |
| CDI Title 10 Ch. 5 | Westlaw (+ PDF rulemaking) | Do not add |
| CRD FEHA Title 2 Div. 4.1 | HTML + PDF + Westlaw | Do not add |
| OSFM Title 19 | PDF + Westlaw | Do not add |
| Coastal Comm. Title 14 Div. 5.5 | Westlaw + PDF rulemaking | Do not add |
| CEC Title 20 | PDF rulemaking | Do not add |
| DIR Title 8 (DLSE subset) | HTML (+ Westlaw) | Do not add |

**Parsers added:** none.
