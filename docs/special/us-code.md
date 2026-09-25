# United States Code (Fair Housing Act and ADA)

How to fetch the official text of the Fair Housing Act and the Americans with Disabilities Act from the United States Code for this project. Checked 2026-09-24 against the Office of the Law Revision Counsel (OLRC) download page. Commercial hosts (Westlaw, Lexis, Justia, FindLaw) are not sources. Do not invent section quotes from this note; quote statute only from a file you have opened.

The Office of the Law Revision Counsel publishes the United States Code under 2 U.S.C. §§ 285 and 285b. Congress created that office in the House. 1 U.S.C. § 204 says what the edition proves. The method is a release-point USLM file. See [authority.md](authority.md).

## Source

- **Publisher.** Office of the Law Revision Counsel of the U.S. House of Representatives.
- **Stable entry.** [Download the United States Code](https://uscode.house.gov/download/download.shtml).
- **Current release point (as of this check).** Through Public Law **119-111** (09/18/2026). Every title on that page is listed as current through 119-111.
- **Preferred format.** XML in the United States Legislative Markup (USLM) schema. Same ranking as the rest of this repo: an XML-like file outranks XHTML and PDF of the same code. The index stores plain text of sections.

OLRC also posts XHTML, PCC, and PDF zips for each title. Those are worse files of the same code. Do not use them when the XML zip is available.

## Concrete download hrefs (this release)

Paths are relative to `https://uscode.house.gov/download/`. They were read from the live download page; they are **not** guessed.

| What | Href on the download page | Absolute URL |
| --- | --- | --- |
| Title 42 XML (USLM) | `releasepoints/us/pl/119/111/xml_usc42@119-111.zip` | `https://uscode.house.gov/download/releasepoints/us/pl/119/111/xml_usc42@119-111.zip` |
| All titles XML (whole Code) | `releasepoints/us/pl/119/111/xml_uscAll@119-111.zip` | `https://uscode.house.gov/download/releasepoints/us/pl/119/111/xml_uscAll@119-111.zip` |

A `HEAD` request to both absolute URLs returned HTTP 200 on 2026-09-24. The files are fetchable now. Do **not** download either zip into the git tree; keep bulk files outside the repo (or under ignored data paths).

The whole-Code XML zip is a real link on the download page (“All titles in the format selected compressed into a zip archive”). It is **not** a permanent URL across releases. The path embeds the release point (`pl/119/111` and `@119-111`). When OLRC posts a later public law, resolve the new href from [download.shtml](https://uscode.house.gov/download/download.shtml) (or [prior release points](https://uscode.house.gov/download/priorreleasepoints.htm)) instead of hardcoding this PL.

Supporting materials on the same host (small; not the Code body):

- USLM schema and stylesheet: `https://uscode.house.gov/download/resources/schemaandcss.zip`
- USLM user guide (PDF): `https://uscode.house.gov/download/resources/USLM-User-Guide.pdf`

## Where FHA and ADA sit (location only)

Both live in **Title 42 — The Public Health and Welfare**. No statutory text is pasted here.

| Act | Code location | Chapter name (OLRC browse) |
| --- | --- | --- |
| Fair Housing Act | 42 U.S.C. chapter 45, starting at §3601 | Fair Housing |
| Americans with Disabilities Act | 42 U.S.C. chapter 126, starting at §12101 | Equal Opportunity for Individuals with Disabilities |

OLRC browse paths used to confirm chapter names (not for ingest):

- `https://uscode.house.gov/view.xhtml?path=/prelim@title42/chapter45&edition=prelim`
- `https://uscode.house.gov/view.xhtml?path=/prelim@title42/chapter126&edition=prelim`

## Positive law

Title 42 is **not** positive law. On the download page, positive-law titles are marked with an asterisk; Title 42 has none. OLRC’s [positive law codification](https://uscode.house.gov/codification/legislation.shtml) page states that Title 42 is a non-positive law title: an editorial compilation of separately enacted statutes, not a title enacted as a whole.

For non-positive law titles, the Code is **prima facie** evidence of the law (1 U.S.C. 204). The **Statutes at Large** (and official slip laws) are the **legal** evidence; if they differ, the Statutes at Large control.

Official hosts for that underlying evidence (point only; do not download for this corpus):

- Slip laws (public and private laws): [https://www.govinfo.gov/app/collection/plaw](https://www.govinfo.gov/app/collection/plaw)
- United States Statutes at Large: [https://www.govinfo.gov/app/collection/statute](https://www.govinfo.gov/app/collection/statute)

Ingest for search still uses the USLM Code text. Treat Title 42 wording as prima facie Code text, not as a positive-law title.

## Corpus file

This publication becomes one SQLite file:

| Place | File |
| --- | --- |
| United States Code | `data/codes/US.sqlite` |

That file is one complete United States Code release-point publication. It is not a Fair Housing / ADA slice, and it is not mixed with California (`data/codes/US-CA.sqlite`). Title 42 XML is enough to cover FHA and ADA; the whole-Code XML zip is the file that fills `US.sqlite` as a full federal corpus. Either way, the unit of storage is the plain text of each section under jurisdiction `US`.

## Parser

**Edition.** `us.usc.UnitedStatesCode` (`Instrument.STATUTE`). Walks USLM `<section>` elements (the primary hierarchical level per the USLM user guide / schema) from an OLRC title XML file or a release-point zip whose members include such a file (e.g. `usc42.xml`). Yields `COUNTRY=US`, `LAW_CODE` = title number, `SECTION_NUM`, and plain `LEGAL_TEXT`. Does not subclass `State`. `UnitedStates` has no `editions` attribute; import the edition from `us.usc`.

**Read:** USLM XML from the title (or all-titles) zip. Nested subsection structure is included in the section's plain text.

**Do not read for ingest:** the companion XHTML zips, PDF zips, or PCC locators, and do not scrape the HTML browse views linked above. Those formats exist on the same official host; they are still the wrong shape when USLM is posted.

## Short summary

| | |
| --- | --- |
| **Source URL** | `https://uscode.house.gov/download/download.shtml` → Title 42 XML `…/xml_usc42@119-111.zip` (current through PL 119-111) |
| **Format** | USLM XML (zip) |
| **Fetchable now?** | Yes (HTTP 200 on the Title 42 and all-titles XML zips, 2026-09-24) |
| **Edition** | `UnitedStatesCode` walks USLM `<section>` elements; `UnitedStatesCode.load` writes `data/codes/US.sqlite` (not XHTML/PDF, not a FHA/ADA-only slice mixed with California). |
