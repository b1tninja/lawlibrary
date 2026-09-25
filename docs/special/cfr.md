# Code of Federal Regulations (all titles)

Shared indexer for federal agency regulations in this project. **One parser for every CFR title** (`us.cfr.CFR`). Do not write a second parser per agency (FEMA, HUD, EPA, …). Agency-specific notes (for example NFIP in Title 44) select parts from the same title file; they do not fork the XML walk. Official hosts only. Commercial hosts are not sources. Do not invent section quotes; quote only text recovered from a file you have opened.

Checked 2026-09-24 against govinfo bulk ECFR XML (Title 44 sample) and the eCFR / NARA legal-status statements.

The Office of the Federal Register publishes this code because 44 U.S.C. § 1510 says it must. The Administrative Committee of the Federal Register, with the President’s approval, requires the codification. An agency’s own statute lets that agency adopt a rule. It does not make the agency the publisher of the CFR. Publication method, and the statute that created each agency, are in [authority.md](authority.md).

## Source

| Role | Host | Notes |
| --- | --- | --- |
| **Parse format** | [govinfo bulk ECFR](https://www.govinfo.gov/bulkdata/ECFR) | One XML file per title: `title-{n}/ECFR-title{n}.xml` |
| Alternate XML | [eCFR versioner API](https://www.ecfr.gov/api/versioner/v1/) | Dated full-title XML; same DIV markup family |
| **Legal edition** | Annual CFR **PDF** and **Text** on govinfo | Official online format; eCFR XML is **not** |

Example Title 44 bulk file (HEAD/GET verified):  
`https://www.govinfo.gov/bulkdata/ECFR/title-44/ECFR-title44.xml`

`CodeOfFederalRegulations.list_editions()` returns that URL pattern for titles 1–50 **without** fetching each title.

Schema / user guide: under `https://www.govinfo.gov/bulkdata/ECFR/resources/`.

## Legal status

GPO / OFR state that the **eCFR is not an official legal edition of the CFR**. Bulk eCFR XML is an editorial compilation updated daily; it is **not** digitally signed and is **not** part of the official online format. The **annual CFR PDF and Text** on govinfo have legal status as parts of that official online format (see [ecfr.gov](https://www.ecfr.gov/), [NARA on the eCFR](https://www.archives.gov/federal-register/cfr/about-ecfr), [govinfo CFR help](https://www.govinfo.gov/help/cfr)).

**Ingest uses eCFR / bulk ECFR XML for section words.** Name and verify against the annual PDF/Text edition. Do not prefer PDF as the parse format when XML of the same title exists.

## XML shape (what the parser reads)

Typical govinfo / eCFR markup (confirmed on a live Title 44 bulk fetch):

| Element | Role |
| --- | --- |
| `DLPSTEXTCLASS` | Document root |
| `IDNO` (`TYPE="title"`) | CFR title number (law code) |
| `DIV5` (`TYPE="PART"`) | Part |
| `DIV8` (`TYPE="SECTION"`) | Section |
| `HEAD` | Section heading |
| `P` | Section paragraphs |

`CFR.sections` walks `DIV8` sections, takes plain text from `HEAD` and `P`, and yields `SECTION_NUM` (from the `N` attribute, without the section sign) and `LEGAL_TEXT`.

Instrument: `Instrument.REGULATION`. Rows stamp `COUNTRY` = `US` and `LAW_CODE` = the title number (for example `44`). **Do not** treat a CFR title as an ISO subdivision or subclass `State`.

## Corpus

One complete title → one SQLite file:

| Place | File |
| --- | --- |
| CFR title *n* | `data/codes/US/cfr/{n}.sqlite` |

Helper: `corpus.cfr_corpus_path(title)`. Do **not** mix titles into `US-CA.sqlite` or into the United States Code file `US.sqlite`. Do **not** commit full title XML into git; keep bulk files under ignored `data/` (or outside the tree). Tests use a synthetic fixture only.

## What is not a source

Justia, FindLaw, Westlaw, Lexis, Fastcase, Cornell LII mirrors used instead of govinfo/eCFR, and HTML scrapes of ecfr.gov browse pages when the bulk or API XML is available.

## Short summary

| | |
| --- | --- |
| **Parse URL pattern** | `https://www.govinfo.gov/bulkdata/ECFR/title-{n}/ECFR-title{n}.xml` |
| **Elements** | `DIV5` PART, `DIV8` SECTION, `HEAD`, `P` (+ `IDNO` for title) |
| **Corpus** | `data/codes/US/cfr/{title}.sqlite` |
| **Legal edition** | Still the **annual CFR** PDF/Text on govinfo |
