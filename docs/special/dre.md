# Regulations of the Real Estate Commissioner

How the project can fetch **Title 10, California Code of Regulations, chapter 6** (Regulations of the Real Estate Commissioner) from an official government host. The index stores plain text. XML-like files outrank HTML and PDF. Commercial hosts are not crawled. Checked 2026-09-24 by reading the official pages. Do not invent regulation text.

The Department of Real Estate is created by Business and Professions Code § 10050. The commissioner adopts these regulations under § 10080. The official compilation is still the Office of Administrative Law’s code under Government Code § 11344. DRE’s PDF is the department’s own book. See [authority.md](authority.md).

## Official CCR (OAL)

[OAL’s CCR publications page](https://oal.ca.gov/publications/ccr/) states that the online Official CCR is provided under contract with Barclays (Thomson Reuters) at `govt.westlaw.com`. Hard copies are sold by Barclays; county clerks, county law libraries, and state depository libraries hold print. OAL updates the official hard-copy and online versions weekly.

That page does **not** offer an OAL bulk XML, zip, FTP dump, or other government-hosted machine file of the CCR. The Westlaw host is the official online compilation OAL points to; it is still a commercial host and is **not** a source for this project.

## DRE Real Estate Law book

DRE publishes a practitioner book at [Real Estate Law](https://www.dre.ca.gov/publications/RealEstateLaw.html) (2026 edition, as of January 1, 2026). Four PDF parts:

| Part | File | What it is |
| --- | --- | --- |
| Statutes | `/files/pdf/relaw/relaw.pdf` | Business and Professions Code §§ 10000–11288 |
| Regulations | `/files/pdf/relaw/regs.pdf` | Title 10 CCR chapter 6 |
| APA | `/files/pdf/relaw/adminlaw.pdf` | Administrative Procedure Act excerpts |
| Excerpts | `/files/pdf/relaw/excerpts.pdf` | Other code excerpts |

The statute half is already covered by California Legislative Counsel **pubinfo** (`LAW_SECTION_TBL` / `CaliforniaCodes`). Do **not** add a second parser for those B&P sections from the DRE PDF.

### Regulations PDF

Best government file for chapter 6 on a non-commercial host:

- Current book: `https://dre.ca.gov/files/pdf/relaw/regs.pdf` (also `https://www.dre.ca.gov/files/pdf/relaw/regs.pdf` and `…/relaw/2026/regs.pdf`; same PDF, ~1.26 MB, `application/pdf`, last-modified 2025-12-27).
- Prior book still posted: `https://www.dre.ca.gov/files/pdf/relaw/2025/regs.pdf` (~1.30 MB, last-modified 2025-02-07).

The PDF is the **department’s own compilation** of Title 10 chapter 6 for the Real Estate Law book. It is not an XML file, not OAL’s official CCR publication, and not a substitute for the Westlaw compilation.

Word (`.doc`/`.docx`), HTML, and XML siblings next to `regs.pdf` return 404. DRE’s publication page and site map link the regulations only as this PDF. No Word, HTML, or XML of chapter 6 was found on `dre.ca.gov`.

### OAL approval notices on DRE

The same Real Estate Law page posts OAL notices and adopted/amended text for individual rulemakings (for example the SB 164 fee package: OAL Matter 2026-0615-04, effective **2026-07-01**). Those PDFs are **session-style regulatory actions**—slip amendments and approval letters—not the compiled chapter. They are not an edition of Title 10 chapter 6.

## Corpus suggestion

Shape under the project rank: **`pdf` only**. A PDF URL list is not an edition. No text or XML-like file of chapter 6 exists on an official host this project will crawl. **The edition stays empty** (`editions = ()`) until a government file yields the words in a preferred shape, or until PDF word-recovery is deliberately built and accepted for this publication.

Do not crawl `govt.westlaw.com`. Do not commit the regulations PDF into git.
