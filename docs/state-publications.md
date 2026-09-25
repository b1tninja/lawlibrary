# Official statute publications

Survey of how each state publishes its **unannotated** code, for a `State` subclass that reads only a government host. The index stores the plain text of each section. Commercial reprints (Justia, FindLaw, Westlaw, Lexis, Fastcase) are not a source. Checked 2026-09-24 by reading the official sites. A later session can change a URL; `accepts` on the edition subclass is what should notice.

PDF and HTML get in the way. A page and a print file both have to be stripped before a word can be stored, and both lose structure on the way. An XML-like file is preferable to either in most cases: the elements are the sections. Rank a state's files by how close they already are to the words:

| Shape | What it is | Index it when |
| --- | --- | --- |
| `text` | Plain text, Word, CSV, or JSON whose body is the statute | The file yields section words |
| `xml` | XML, SGML, CAML, or another XML-like body | The elements yield section words. Prefer this over HTML or PDF of the same code |
| `html` | Official section or chapter pages, or a zip of those pages | No XML-like file exists, and the tags can be stripped to those words. A bulk zip of HTML is still HTML |
| `pdf` | A finite set of official title or volume PDFs | No text or XML-like file exists, and the words can be recovered. A URL list alone is not an edition |
| `none` | The public code is a commercial host | Never. There is no government text to index |

## Bulk files

These states publish the whole code as one download or API. Prefer plain text in that download, then an XML-like file. California's zip is CAML, which is the XML-like file for that state. A sibling zip of HTML or PDF is a worse file of the same code.

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
| Virginia | Code Commission / LIS | Per-title CSV and PDF from `https://law.lis.virginia.gov/law-library/`. The library page lists those two formats. `/jsonapi/` and `/xmlapi/` did not return a file. Annotations excluded. Updated July 1 |

## Format comparison

Checked 2026-09-25 by downloading each bulk format the publisher posts, one title or one code where the set is per-volume. The file to ingest is the one that already has a section element and the heading path. PDF stays a print copy.

| Publication | Formats on disk | Ingest |
| --- | --- | --- |
| United States Code, title 1 | USLM XML (already). HTML zip is `PRELIMusc01.htm` only (no `<section>`). PCC is a locator prelude. PDF is one print file | USLM XML |
| CFR title 1 | eCFR XML (`DIV8`). Annual `CFR-2025-title1-vol1.xml` is `CFRDOC / TITLE / CHAPTER / PART / SECTION` with `SECTNO` and `P` | Annual CFR XML. eCFR still parses |
| Texas Agriculture Code | `AG.htm.zip` (already), `AG.pdf.zip` (95 chapter PDFs), `AG.doc.zip` (95 docx, no heading styles) | HTML zip |
| Colorado | `crs2026-htm.zip` (already), `crs2026-docx.zip` (48 title docx, no heading styles), `crs2026-pdf.zip` | HTML zip. SGML is still by request |
| Virginia title 1 | `CoVTitle_1.csv` (already; title, part, chapter, article columns), `Title1.pdf` | CSV |
| New Jersey | `STATUTES-TEXT.zip` contains `STATUTES.TXT` and `STATUTES.RTF` | Plain text |

## Official PDF sets

These states publish the code as title PDFs. That is a print copy, not text in the index. Delaware also has HTML on the same host. A subclass does not gain an edition from a PDF URL list.

A second pass looked for a bulk file or raw text behind the title PDFs. None of these six publishes a current XML or zip of the whole code.

| State | What else exists | Bulk raw statutes |
| --- | --- | --- |
| Alaska | Title index at `akleg.gov/basis/statutes.asp`. BASIS public API is bills, members, committees, and sessions, not the code. The Folio infobase at `regulations.akleg.gov/statutes` says it is unofficial. | No. The title PDFs are the public text. |
| Maine | The Revisor's title pages offer PDF and Word for a title, chapter, or section. A [Statute XML](https://legislature.maine.gov/documents) set was filed in 2017 and stops at the 127th Legislature. | No current bulk. Word files are raw text, one title or chapter at a time. Current XML is not posted. |
| Oklahoma | Legislature title PDFs at `OK_Statutes/CompleteTitles/os{title}.pdf`. The Secretary of State certifies the unannotated code, and that publication is West's site `govt.westlaw.com/okjc`. Enrolled bills from 2001 on are at `sos.ok.gov/gov/legislation.aspx`. OSCN citationizes the same statutes. | No legislature XML or zip. The certified code is a commercial host. The title PDFs remain the government files. |
| Pennsylvania | `palegis.us` section search says it returns a PDF only. `palegis.us/data` is bill-history XML from 1969, not the consolidated statutes. The Legislative Reference Bureau publishes the official consolidated statutes. | No. Slip laws and pamphlet laws are session laws, not the code. |
| Washington | The Statute Law Committee says the certified PDFs in the RCW archive are the official publication. `app.leg.wa.gov/RCW/default.aspx?cite=` is the Code Reviser's own HTML, updated twice a year, and is not that official publication. | No bulk file. The cite HTML is raw text on a government host. The certified copy is still the PDF. |
| Wyoming | Text-only title PDFs under `/statutes/compress/`. A download-format page lists the same titles. The Legislative Service Office sells the titles as Word on a USB drive. The annotated site is Lexis, for non-commercial use. | No public XML or zip. The compress PDFs are the public text. The Word set is not a posted file. |

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
