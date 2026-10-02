# NFPA standards in California law

How NFPA 13 (sprinkler installation) and NFPA 25 (inspection, testing and maintenance of water-based systems) become law in California, and what this project reads of them. Checked 2026-09-29. Code: `adoption.py`, `us/ca/title24/`, `us/ca/title19.py`.

## The chain

```
NFPA 13-2025 ─► IFC 2024 ─► 2025 California Fire Code (Title 24 Part 9), effective 2026-01-01
                              903.3.1.1 → "NFPA 13 as amended in Chapter 80"
                              Chapter 80 → "NFPA 13—25 … as amended*", California's amendments printed there
                            ─► local ordinance amends CFC sections (e.g. Sacramento Metro Fire Ord. 2025-02)
                                 → ratified by the city or county (HSC 13869.7), filed with BSC (HSC 17958.7, 18941.5)

NFPA 25-2011 ─► Title 19 CCR §901: incorporated by reference, State Fire Marshal's amendments written into §901
                 ("NFPA 25, 2013 California Edition"); §904 inspection duties; authority HSC 13195
               ◄─ CFC 901.6 / 901.6.1 and Chapter 80 "NFPA 25—13CA" point to it
```

- The State Fire Marshal adopts the Fire Code's fire and life-safety standards (HSC 13143). The Building Standards Commission approves and publishes them (HSC 18930 et seq.).
- Title 19 Division 1 is the State Fire Marshal's own APA regulation, not a Title 24 part.
- The 2025 Building Code (Part 2) Chapter 35 dropped its California amendments to NFPA 13, because NFPA 13-2025 already contains them. The Fire Code's Chapter 80 still prints its amendments.

## Which date picks the edition

| Event | Date that governs | Rule |
| --- | --- | --- |
| `Event.PERMIT_APPLICATION` | The day the building permit was applied for | HSC 18938.5 |
| `Event.INSPECTION` | The day of the inspection | Title 19 and CFC 901.6 in force that day |

| Fire Code edition | Effective | Permits applied for | NFPA 13 | NFPA 25 |
| --- | --- | --- | --- | --- |
| 2022 | 2023-01-01 | through 2025-12-31 | 13-2022, as amended | 2013 California edition (2011-based) |
| 2025 | 2026-01-01 | from 2026-01-01 | 13-2025, as amended | 2013 California edition (2011-based) |

The Title 19 NFPA 25 adoption is operative 2014-08-28 (Register 2014, No. 35, per the section's history note). NFPA's current national edition of NFPA 25 is not adopted in California as far as was found.

The 2025 intervening-cycle supplement takes effect 2027-07-01. It is not loaded.

## What is read

| Text | Source | Shape | Loaded |
| --- | --- | --- | --- |
| California Fire Code 2025 | Public.Resource.Org scan, [gov.ca.bsc.fire.2025](https://archive.org/details/gov.ca.bsc.fire.2025) (includes January 2026 errata) | OCR plain text (`_djvu.txt`) | `data/codes/US-CA/title24/2025/9.sqlite` |
| California Fire Code 2022 | Public.Resource.Org scan, [2022californiafi00unse](https://archive.org/details/2022californiafi00unse) | OCR plain text | `data/codes/US-CA/title24/2022/9.sqlite` |
| Chapter 80 referenced standards | The same scans | Parsed into the `reference` table: designation, edition, title, amended, citing sections | Same files |
| California's amendments to a standard | Chapter 80 "Amended Sections as follows" | A row numbered by the standard (`NFPA 13`) | Same files |
| Title 19 §901 adoption of NFPA 25 | Recorded by hand in `us/ca/title19.py` | An `Adoption` record | In code |

Each scan is OCR. A word can be misread and a table is flattened to lines. A hit carries `ocr: true`. The parser drops page furniture: the ICC order number, the licence watermark, running heads, page numbers and the nonregulatory matrix adoption tables. Appendix chapters are not read; they bind only where a local ordinance adopts them.

`python` use:

```python
from us.ca.title24 import EDITIONS, fetch, section, governing
from us.ca.title24.fire import CaliforniaFireCode
for edition in EDITIONS:
    CaliforniaFireCode().load(fetch(edition))
section('9', '903.3.1.1', on='2026-03-01')
section('9', 'NFPA 13')            # California's amendments, Chapter 80
governing('NFPA 13', on='2024-06-01')
governing('NFPA 25', event='inspection')
```

MCP tools: `building_standard(part, section, edition, on)` and `standard_adoption(standard, on, event)`.

Misses:

| Reason | Meaning |
| --- | --- |
| `unknown_book` | Not a Title 24 part |
| `no_edition` | No known edition covers that edition year or day |
| `not_indexed` | The edition is known but its file is not loaded |
| `not_in_index` | The loaded edition has no such number |
| `not_adopted` | No loaded adopter names that standard on that day |
| `standard_absent` | The standard's own words are not held (always, today) |
| `bad_request` | The date or event could not be read |

When Title 19 and the Fire Code both name NFPA 25, both adoptions are returned, with each edition as that adopter writes it (`2011`, `2013 CA`).

## What is not read

- **NFPA's own text.** NFPA's free viewer and NFPA LiNK need an account, forbid copying, and offer no bulk file. They are never scripted.
- **NFPA 13-2025, 13-2022, 25-2023, 25-2026.** No lawful public copy exists. Public.Resource.Org has posted NFPA 13-2002 and 2010, 13D-2010, 13R-2010, 25-2002 and 25-2011 (`gov.law.nfpa.*`). NFPA 25-2011 is the base of California's Title 19 edition and is the strongest candidate to load next.
- **Title 19 text.** OAL's official CCR is Westlaw. The State Fire Marshal's [final-text PDF](https://34c031f8-c9fd-4018-8c5a-4159cdff6b0d-cdn-endpoint.azureedge.net/-/media/osfm-website/what-we-do/code-development-and-analysis/title-19-development/finaltextofregs-nfpa25-2011_8-27-2014corrected_resubfinal.pdf) is strikeout and underline, so its OCR mixes deleted and added words. Public.Resource.Org's Title 19 scan (`gov.ca.ccr.19`) is from 2008. The Fire Code reprints some Division 1 subsections, including §904(a)(1), §904.1 and §904.2, under `[California Code of Regulations, Title 19, Division 1, §…]` markers. Those can be split out of the Fire Code later.
- **ICC viewers, Errata Central, UpCodes, and the commercial hosts in AGENTS.md.**

## Why the scans are allowed

Public.Resource.Org posts codes that governments adopted as law, on a noncommercial basis. The courts that have ruled support reading them:

- *Veeck v. SBCCI*, 293 F.3d 791 (5th Cir. 2002) (en banc): a model code enacted as law may be copied as the law.
- *Georgia v. Public.Resource.Org*, 590 U.S. 255 (2020): text a government official writes is not copyrightable. This covers California's own amendments (Chapter 80, Title 19 §901).
- *ASTM v. Public.Resource.Org*, 82 F.4th 1262 (D.C. Cir. 2023): noncommercial posting of standards incorporated by reference is fair use. NFPA was a plaintiff.
- *ICC v. UpCodes* (S.D.N.Y. 2020): I-Codes as adopted are likely public domain.
- *ASTM v. UpCodes* (3d Cir. 2026-04-07): affirmed denial of a preliminary injunction against posting incorporated standards.

The Pro Codes Act (H.R. 4009, 119th Congress) would let a standards body keep copyright where it offers free online viewing. It is pending. If it passes, this page and the parser's sources are revisited.

## Local adoption around Sacramento

- **Sacramento Metropolitan Fire District Ordinance 2025-02** adopted the 2025 Fire Code on 2025-11-13 ([certified PDF](https://metrofire.ca.gov/files/fca1dc973/CERTIFIED+ORD+2025-02+2025+CALIFORNIA+FIRE+CODE,+TITLE+24,+CODE+OF+REGULATIONS,+PART+9.pdf)). It amends Fire Code 901.4.7 and 903.x sprinkler sections, not NFPA 13 or 25 directly.
  - Its only Chapter 80 change adds NFPA 1123.
  - It takes effect only as ratified by the county or city (HSC 13869.7).
- **City of Sacramento:** Chapter 15.36 still reads as the 2022 Fire Code. Ordinance 2025-0031 does not touch it.
- **Filings:** BSC's [2025 ordinance filings page](https://www.dgs.ca.gov/BSC/Codes/2025-Ordinances) listed no Sacramento city or county filing on 2026-09-29.
- **Not yet recorded:** local ordinances are not yet `Adoption` records. A local amendment takes effect 180 days after BSC publishes the code, and not before it is filed (HSC 17958.7, 18941.5). From 2025-10-01 to 2031-06-01, stricter local residential standards are barred except as HSC 18941.5(c) lists.

## Still open

- Whether OSFM has a rulemaking pending to adopt a newer NFPA 25. Its Title 19 page refused automated fetches.
- The ratifying county ordinance for Metro Fire 2025-02, and whether the City has adopted 2025 Fire Code amendments.
- Older Fire Code editions (2007–2019) are scanned (`gov.ca.bsc.title24.part09`, `gov.ca.bsc.title24.2010.part09`, `gov.ca.bsc.2013.09`, `gov.ca.bsc.title24.2016.09`, `2019californiafi00unse`) and can join `EDITIONS` with their dates.
