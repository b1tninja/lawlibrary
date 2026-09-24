# Official statute publications

Survey of how each state publishes its **unannotated** code, for a `State` subclass that reads only a government host. Commercial reprints (Justia, FindLaw, Westlaw, Lexis, Fastcase) are not a source. Checked 2026-09-24 by reading the official sites. A later session can change a URL; `accepts` on the edition subclass is what should notice.

Four shapes, same as the publication base:

| Shape | What the subclass downloads |
| --- | --- |
| `bulk` | One archive, a file tree, or an official API that returns the whole code |
| `pdf` | A finite set of official title or volume PDFs |
| `html` | Official section or chapter pages, no bulk file |
| `none` | The public code is a commercial host. No government corpus to index |

## Bulk, closest to California

These can follow `California`: a distribution URL, an edition parser, a local index.

| State | Publisher | Distribution |
| --- | --- | --- |
| California | Legislative Counsel | `https://downloads.leginfo.legislature.ca.gov/` `pubinfo_YYYY.zip`. Code tables from 2011 on |
| Colorado | Revisor / OLLS | Title zips, e.g. `https://olls.info/crs/crs2026-htm.zip` (HTML, PDF, DOCX). HTML includes annotations. Unannotated SGML is by request, not a public URL |
| Florida | Division of Law Revision | `https://www.leg.state.fl.us/Statutes/FLLawDL2026.zip` plus chapter HTML. The zip is the official Windows browser; an open XML export was not documented |
| Illinois | Legislative Information System | `https://www.ilga.gov/ftp/ILCS/` directory of section HTML, not one zip. Readme says the print at the Secretary of State is the official copy |
| Indiana | Legislative Services Agency | Downloads page offers a full-code HTML zip and a PDF+HTML zip. The file URLs were not confirmed to return a zip (the site returned the app shell) |
| Iowa | Legislative Services Agency | Official code is eight volume PDFs. Unofficial chapter XML: `/docs/publications/ICC/2026/attachments/{chapter}_slim.xml` |
| Michigan | Legislature | `https://www.legislature.mi.gov/documents/mcl/` chapter XML (`BodyText`), plus PDF. Not one zip |
| Nebraska | Revisor | Legislature GitHub `nelegislature/LegalDocs` (statute XML, no case notes). HTML browse also has an Annotations block to skip |
| New Jersey | Legislature | `https://pub.njleg.gov/statutes/STATUTES-TEXT.zip` plain text and RTF, rebuilt weekdays at 2 AM. Unannotated |
| New York | LBDC, via Senate | `https://legislation.nysenate.gov/api/3/laws/{lawId}?full=true`. Free API key. Weekly from LBDC. Not a zip |
| North Dakota | Legislative Council | `https://ndlegis.gov/api/data/century_code.json` one JSON document, no key. Also chapter PDFs |
| Texas | Legislative Council | `https://statutes.capitol.texas.gov/download` and `StatuteCodeDownloads.json`. Per-code zips of HTML, PDF, and Word on `tcss.legis.texas.gov`. Statutory text, no annotations |
| Utah | Legislative Research | `https://glen.le.utah.gov/code/.../<token>` XML. Developer token. Docs say check at most daily |
| Virginia | Code Commission / LIS | Per-title CSV and PDF from `https://law.lis.virginia.gov/law-library/`, plus `/jsonapi/` and `/xmlapi/`. Annotations excluded. Updated July 1 |

## Official PDF sets

A subclass lists titles and fetches each file. No crawl.

| State | Distribution |
| --- | --- |
| Alaska | `https://www.akleg.gov/statutesPDF/Title-{N}.pdf` |
| Delaware | `https://delcode.delaware.gov/title{N}/title{N}.pdf` and HTML. Site is prepared with Lexis; the host is the state's |
| Maine | `https://www.mainelegislature.org/legis/statutes/{title}/title{title}.pdf` |
| Oklahoma | `https://www.oklegislature.gov/OK_Statutes/CompleteTitles/os{title}.pdf`. The certified unannotated code on the SOS site is a West portal; use these PDFs instead. `robots.txt` disallows PDFs |
| Pennsylvania | `https://www.legis.state.pa.us/WU01/LI/LI/CT/PDF/{title}/{title}.PDF` and matching HTML. Not Purdon's |
| Washington | Certified title PDFs, `https://lawfilesext.leg.wa.gov/Law/RCWArchive/2025/pdf/`. Online RCW twice a year |
| Wyoming | Text-only titles, `https://wyoleg.gov/statutes/compress/title01.pdf`. The Lexis annotated feed is a separate, non-commercial contract |

## Official HTML, no bulk file

Practical ingest is a crawl of the government host, polite to any crawl delay. Several of these pages say the print edition is the official copy.

Alabama (client-rendered), Arizona (crawl-delay 120; `/xml/` disallowed), Connecticut, Hawaii, Idaho (statute claims a royalty for commercial reproduction), Kansas (also a public per-section JSON API), Kentucky (commercial use needs an LRC agreement), Louisiana, Maryland, Massachusetts, Minnesota (database copies sold on request), Missouri, Montana (paid Folio dump is annotated), Nevada, New Hampshire, New Mexico (Norma terms forbid automated bulk download), North Carolina (chapter HTML and PDF; pages say "Not Official"), Ohio (`robots.txt` disallows `/`; authenticated PDF per section), Oregon (chapter HTML; print ORS is official), Rhode Island (daily HTML), South Carolina (chapter HTML and docx), South Dakota (JSON API under `/api/Statutes/`), Vermont (legislature HTML is labeled an unofficial copy of the annotated print), West Virginia (HTML per section, PDF per chapter; print is official), Wisconsin (HTML and PDF per chapter, annotations included and must be split off).

## No government corpus

The legislature sends the public to a commercial host. There is nothing for this project to download.

| State | What the official site links to |
| --- | --- |
| Arkansas | Lexis Advance for the Arkansas Code |
| Georgia | Lexis for the unannotated Code |
| Mississippi | Lexis for the Code. Session-law PDFs exist and are not the Code |
| Tennessee | Lexis for the Code. The legislature publishes only the annual Code Bill PDFs, which are that year's codification, not the whole TCA |
