# Who publishes, and who authorized them

Each corpus has two different statutes. One creates the agency and lets it regulate. The other tells a publisher how the compiled text is issued. The index follows the publisher’s official file. It does not treat an agency brochure as that file.

Citations below are locations. They are not quotations.

## United States Code

| | |
| --- | --- |
| Publisher | Office of the Law Revision Counsel, in the House of Representatives |
| Who authorized the office | 2 U.S.C. § 285. The Law Revision Counsel is appointed by the Speaker (2 U.S.C. § 285c). The office was enacted into permanent law by Pub. L. 93-554 from H. Res. 988, 93d Congress |
| Duty to publish | 2 U.S.C. § 285b: prepare and publish the United States Code, including titles not yet enacted as positive law, with cumulative supplements |
| What the edition is | 1 U.S.C. § 204. The current Code is prima facie evidence of the general and permanent laws. A title enacted as positive law is legal evidence. Title 42 is not positive law, so the Statutes at Large control if they differ |
| Method | A release point on [uscode.house.gov/download](https://uscode.house.gov/download/download.shtml). USLM XML is the file this project parses. XHTML and PDF on the same page are the same edition in a worse shape |

## Code of Federal Regulations and the Federal Register

| | |
| --- | --- |
| Publisher of the Code | Office of the Federal Register prepares and publishes the codification (44 U.S.C. § 1510(d)). The Administrative Committee of the Federal Register, with the approval of the President, requires the codification and regulates its form (44 U.S.C. § 1510(a)–(c)) |
| Publisher of the daily register | Government Publishing Office publishes the Federal Register (44 U.S.C. § 1504). Documents are filed with the Office of the Federal Register |
| What the edition is | The annual Code of Federal Regulations is the special edition of the Federal Register required by § 1510. The eCFR is an electronic update the Office may make under § 1510(c). GPO states that eCFR XML is not the official legal edition. The annual CFR PDF and text on govinfo are |
| Method | One title XML file: `https://www.govinfo.gov/bulkdata/ECFR/title-N/ECFR-titleN.xml`, stored as `data/codes/US/cfr/{title}.sqlite`. The Federal Register bulk XML is the daily amendment, not a second copy of the Code |

An agency does not publish the CFR. It adopts a rule under its own statute and the Administrative Procedure Act (5 U.S.C. § 553). The rule is published in the Federal Register and then codified.

## Federal agencies in the manager index

| Agency | Who authorized it | Rulemaking this project cares about | Compiled in |
| --- | --- | --- | --- |
| Department of Housing and Urban Development | Department of Housing and Urban Development Act, 42 U.S.C. § 3531 et seq. | Fair Housing Act regulations, 42 U.S.C. §§ 3608, 3614a | 24 CFR |
| Department of Justice | Attorney General, 28 U.S.C. § 501 | ADA Title II, 42 U.S.C. § 12134; ADA Title III, 42 U.S.C. § 12186 | 28 CFR |
| Federal Emergency Management Agency | Homeland Security Act, 6 U.S.C. § 313. The flood program is the National Flood Insurance Act, 42 U.S.C. § 4001 et seq. | 42 U.S.C. § 4121 and related NFIP provisions | 44 CFR |
| Federal Communications Commission | Communications Act of 1934, 47 U.S.C. §§ 151, 154 | Over-the-air reception devices | 47 CFR |
| Environmental Protection Agency | Reorganization Plan No. 3 of 1970 | Lead-based paint, including the Residential Lead-Based Paint Hazard Reduction Act | 40 CFR, and HUD’s joint rules in 24 CFR part 35 |
| Occupational Safety and Health Administration, in the Department of Labor | Occupational Safety and Health Act, 29 U.S.C. § 651 et seq. The Department of Labor is 29 U.S.C. § 551 | Workplace standards, 29 U.S.C. § 655 | 29 CFR |

## California regulations

| | |
| --- | --- |
| Publisher of the code | Office of Administrative Law. Government Code § 11344 requires the official compilation, printing, and publication of the California Code of Regulations, and a free Internet text. The office may contract that Internet text to a private entity. It has contracted Barclays (Thomson Reuters). That host is the official online CCR and is still not a source this project crawls |
| How a rule becomes law | The agency adopts it under the Administrative Procedure Act, Government Code § 11340 et seq. OAL reviews it. It is filed with the Secretary of State. It is then compiled into the CCR |
| Method | Weekly official CCR. No government bulk XML was found. Agency PDF books are department compilations, not that official code |

| Agency | Who authorized it | What it adopts | Where the words went |
| --- | --- | --- | --- |
| Department of Real Estate | Business and Professions Code § 10050, in the Business, Consumer Services, and Housing Agency. The commissioner may adopt regulations under § 10080 | Title 10, California Code of Regulations, chapter 6 | Official text is the OAL CCR. DRE also posts its own PDF book |
| California Building Standards Commission | Health and Safety Code § 18901 (California Building Standards Law) and § 18920 (commission in the Department of General Services). Building standards are approved under § 18930 et seq. | Title 24, the California Building Standards Code. Health and Safety Code § 18902 says that name and Title 24 are the same code | Triennial edition. Parts 2 and 9 are published by the International Code Council under copyright. OAL’s CCR excludes Title 24 |
| Department of Housing and Community Development | Health and Safety Code § 50400. State Housing Law begins at § 17910 | Housing regulations, Title 25, and amendments that feed Title 24 | Westlaw CCR, plus PDF rulemaking files |
| Contractors State License Board | Business and Professions Code § 7000.5 | Contractors’ State License Law regulations | PDF law book and the Westlaw CCR |
| Department of Insurance | Insurance Code § 12900 | Insurance regulations, Title 10 | Westlaw CCR and PDF rulemaking |
| Civil Rights Department | Government Code § 12901. Fair Employment and Housing Act begins at § 12900 | FEHA regulations, Title 2 | HTML, PDF, and the Westlaw CCR |
| Office of the State Fire Marshal | Health and Safety Code § 13100 | Fire and life-safety regulations, including material that is adopted into Title 24 | PDF and the Westlaw CCR |
| California Coastal Commission | Public Resources Code § 30300. The Coastal Act begins at § 30000 | Coastal regulations, Title 14 | Westlaw CCR and PDF rulemaking |
| California Energy Commission | Public Resources Code § 25200 | Energy regulations, including building-energy standards adopted through Title 24 | PDF rulemaking |
| Department of Industrial Relations | Labor Code § 50 | Labor standards and wage orders | HTML sections and the Westlaw CCR |
