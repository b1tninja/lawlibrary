# Title 24, Parts 2 and 9

How (not) to fetch the California Building Code and California Fire Code for this project. Checked 2026-09-24 against the Building Standards Commission Codes page, the CBSC FAQ, the 2025 Guide to Title 24, Information Bulletin 25-01, and the Office of Administrative Law’s CCR note. Official government text only. The index stores plain text. An XML-like file outranks HTML and PDF of the same code. Do not invent section text.

The California Building Standards Commission continues under Health and Safety Code §§ 18901 and 18920. It approves building standards under § 18930 et seq. Health and Safety Code § 18902 provides that Title 24 and the California Building Standards Code are the same code. The commission publishes that code on a triennial cycle. Parts 2 and 9 are then issued by the International Code Council. See [authority.md](authority.md).

## Verdict

There is **no government bulk file** of Title 24 Part 2 or Part 9. The adopted words live only in the copyrighted ICC publication (viewable online, not downloadable as the full code). A Part 2 or Part 9 edition stays `editions = ()`. A later parser must refuse ICC, NFPA, and IAPMO viewers, their errata/supplement PDFs, purchased code PDFs, and any scrape or reconstruction of those hosts.

## What Parts 2 and 9 are

Title 24 of the California Code of Regulations is the California Building Standards Code. It is maintained by the California Building Standards Commission (CBSC), not by the Office of Administrative Law. OAL’s online and printed CCR **exclude** Title 24 ([oal.ca.gov/publications/ccr/](https://oal.ca.gov/publications/ccr/)).

| Part | Name | Model base (2025 edition) | Publisher |
| --- | --- | --- | --- |
| 2 | California Building Code (Volumes 1 & 2) | 2024 International Building Code | ICC |
| 9 | California Fire Code | 2024 International Fire Code | ICC |

CBSC’s Codes page: [https://www.dgs.ca.gov/BSC/Codes](https://www.dgs.ca.gov/BSC/Codes). Part links go to the publisher’s site (for Parts 2 and 9, `codes.iccsafe.org`), not to a DGS raw file.

The California Building Standards Code is a mix of (1) model-code text adopted without change, (2) model-code text adapted for California, and (3) California-only amendments. Parts 2 and 9 are in the second category: IBC/IFC pre-assembled with California amendments. Those amendments are not posted by the state as a segregable bulk of Part 2 or Part 9 section text.

## Which edition is current

| Edition | Published | Statewide effective | Permit applications |
| --- | --- | --- | --- |
| 2025 | 2025-07-01 | 2026-01-01 | On or after 2026-01-01 |
| 2022 | 2022-07-01 | 2023-01-01 | On or before 2025-12-31 |

Health and Safety Code section 18938.5: the codes in effect on the date of building-permit application govern the plans and construction. Information Bulletin 25-01 states that rule for the 2025 / 2022 handoff. The FAQ’s “Which edition of Title 24 applies…” answer is the same point.

## Copyright and the online viewers

FAQ (December 2022), “Is Title 24 available online, or must it be purchased?”: the Codes tab links to ICC, IAPMO, and NFPA; the codes are **viewable online** but **not downloadable** because of copyright agreements with the publishers. Purchase (or a State Document Depository Library) is how one gets a working copy for design, plan review, or inspection.

2025 Guide to Title 24, “How to Obtain Supplements and Errata”: CBSC links to downloadable errata and supplements, but “the original code text cannot be downloaded and printed due to copyright protections.”

Westlaw’s CCR help (linked from OAL’s CCR path) likewise says Title 24 contains copyrighted model-publisher material and is published separately.

**Do not crawl** the ICC (or NFPA/IAPMO) online viewers. Naming a viewer URL is not a source for this project.

For the 2025 edition, the Codes page points Part 2 and Part 9 at ICC viewers such as:

- Part 2: `https://codes.iccsafe.org/content/CABC2025P2`
- Part 9: `https://codes.iccsafe.org/content/CAFC2025P2`

Those are publisher hosts. They are not government files.

## What the state posts for free (not the adopted Part 2 / Part 9 text)

Distinguish these from the model-code base and from the full adopted CBC/CFC.

### Information bulletins (government PDFs on `dgs.ca.gov`)

Announce publication, effective dates, errata, and supplements. Examples:

- [IB 25-01](https://www.dgs.ca.gov/-/media/Divisions/BSC/06-News/Information-Bulletins/2025/BSC-Bulletin-25-01-FINAL.pdf) — 2025 edition published; effective 2026-01-01; 2022 still applies to permits filed through 2025-12-31
- [IB 26-01](https://www.dgs.ca.gov/-/media/Divisions/BSC/06-News/Information-Bulletins/2026/BSC-Information-Bulletin-26-01-Errata.pdf) — 2025 errata (including Parts 2 and 9), effective 2026-01-01; summarizes topics, does not replace the code books

Bulletins are state notices. They are not a bulk Part 2 or Part 9 corpus.

### California code-change summaries (government PDF / HTML)

Narrative summaries of substantive California amendments by part and chapter. They describe changes; they are not the published section words of Part 2 or Part 9.

- HTML: [https://www.dgs.ca.gov/BSC/Resources/2025-Title-24-California-Code-Changes](https://www.dgs.ca.gov/BSC/Resources/2025-Title-24-California-Code-Changes)
- PDF: [https://www.dgs.ca.gov/-/media/Divisions/BSC/05-Resources/Guidebooks/2025-Title-24-CA-Code-Changes---New-07-25.pdf](https://www.dgs.ca.gov/-/media/Divisions/BSC/05-Resources/Guidebooks/2025-Title-24-CA-Code-Changes---New-07-25.pdf)

Older cycle summaries (2022 intervening / 2022 triennial) sit under the same Resources / Guidebooks area. Same limit: summary, not the adopted code.

### Guides and FAQ (government PDFs)

- [2025 Guide to Title 24](https://www.dgs.ca.gov/-/media/Divisions/BSC/05-Resources/Guidebooks/2025-Guide-toTitle-24---6th-Edition.pdf)
- [CBSC FAQ](https://www.dgs.ca.gov/-/media/Divisions/BSC/05-Resources/FAQs-and-Other/FAQ-12-19-22-Final-Print-Version-rev-06-23.pdf)

Education and process. Not Part 2 / Part 9 section text.

### Errata and supplements for Parts 2 and 9

CBSC’s Codes page lists errata (and, for older editions, supplements) under each part. For Parts 2 and 9 those hrefs resolve to **ICC Errata Central** on `iccsafe.org` (publisher PDFs of replacement pages), not to `dgs.ca.gov` media. Example pattern (2025 Part 2 Vol. 1 errata, Part 9 errata): `https://www.iccsafe.org/wp-content/uploads/errata_central/…`. Do not fetch or index those. They are publisher packages of copyrighted code pages.

Contrast: some other parts’ packets sit on other publisher hosts (IAPMO) or, for Part 3 errata, on DGS media. That does not create a government Part 2 or Part 9 bulk file.

The Codes page for 2025 Part 3 also links “California-specific amendments only.” Parts 2 and 9 have no parallel government-only amendments file on that page.

### Rulemaking packages

CBSC’s site under `/03-Rulemaking/` holds Express Terms, statements of reasons, and meeting materials for triennial and intervening cycles. Those are government rulemaking records about proposed California amendments. They are not a published Part 2 or Part 9 edition and are not a substitute for the adopted code text.

## Statutes that adopt or apply Title 24 (already in the code corpus)

Health and Safety Code provisions around sections 17950 and 17958 (State Housing Law) and Division 13, Part 2.5 commencing with section 18901 (California Building Standards Law, including 18902, 18938, 18938.5) establish that Title 24 applies statewide and how local amendments work. Those short statutes are already in the California statute publication (`pubinfo` / `CaliforniaCodes`). They are **not** the Building Code or the Fire Code. Do not treat them as a stand-in for Part 2 or Part 9.

## What a later parser must refuse

- ICC online code viewers and any crawl, scrape, or mirror of them (including URLs under `codes.iccsafe.org` linked from the Codes page)
- ICC Errata Central PDFs for Parts 2 and 9 (and any other ICC-hosted Title 24 packets)
- NFPA and IAPMO viewers or downloads (other Title 24 parts; same copyright posture)
- Purchased or library PDF/HTML of Part 2 or Part 9 committed into git or treated as a government bulk source
- Invented or paraphrased “quotes” of CBC/CFC sections without an allowed government file of those words
- Using HSC §§ 17950 / 17958 (or Building Standards Law) as if they were Part 2 or Part 9

## Shape for this project

| Question | Answer |
| --- | --- |
| Government XML / CAML / zip of Part 2 or Part 9? | No |
| Government HTML or PDF of the full adopted Part 2 or Part 9? | No |
| `editions` for Part 2 / Part 9 | Stay empty |
| Closest official state files | Bulletins, change summaries, guides, FAQ, rulemaking PDFs on `dgs.ca.gov` — metadata and narrative only, not the CBC/CFC corpus |
