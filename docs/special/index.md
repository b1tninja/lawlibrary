# Official sources

Every corpus and every agency name in this tree comes from a government publisher. A commercial host is not a source, even when a state calls that host its official compilation. Agency names are copied from the state’s own directory. They are not translated into a shared title.

## Publications

| What | Who publishes it | Authority | File this project parses | Where it is written up |
| --- | --- | --- | --- | --- |
| United States Code | Office of the Law Revision Counsel | 2 U.S.C. §§ 285, 285b; evidentiary status 1 U.S.C. § 204 | Release-point USLM XML on [uscode.house.gov/download](https://uscode.house.gov/download/download.shtml) | [us-code.md](us-code.md) |
| Code of Federal Regulations | Office of the Federal Register | 44 U.S.C. § 1510 | eCFR title XML on govinfo. The annual PDF is the legal edition | [cfr.md](cfr.md) |
| Federal Register | Government Publishing Office | 44 U.S.C. § 1504 | Bulk XML. Daily amendments, not the compiled code | [nfip-cfr.md](nfip-cfr.md) |
| Federal departments’ rules | The department adopts them. The Federal Register publishes them | Each department’s organic statute, listed in [authority.md](authority.md) | The CFR title, not the department’s brochure | [federal-agencies.md](federal-agencies.md) |
| California statutes | Legislative Counsel | The Legislature’s pubinfo distribution | `pubinfo_YYYY.zip` | [layout.md](../layout.md) |
| California Code of Regulations | Office of Administrative Law | Government Code § 11344 | No government bulk XML. The online compilation is Barclays and is not crawled | [california-agencies.md](california-agencies.md) |
| California Building Standards Code | California Building Standards Commission | Health and Safety Code §§ 18901, 18920, 18930 | No government bulk file of Parts 2 and 9 | [title-24.md](title-24.md) |
| Real Estate Commissioner regulations | Department of Real Estate, compiled by OAL | Business and Professions Code §§ 10050, 10080 | Department PDF only | [dre.md](dre.md) |

Who created each body, as distinct from who publishes the compilation, is [authority.md](authority.md).

## State agency directories

A state’s agencies are the names on that state’s official roster. The usual publisher is the Secretary of State, the Governor’s office, or the state portal. Each directory URL and the printed names are recorded under `state-agencies/` as those pages are read.

California is the roster already in hand:

| Range | File | Publisher |
| --- | --- | --- |
| A–F | [ca-roster/a-f.md](ca-roster/a-f.md) | Secretary of State, [2026 state agencies PDF](https://admin.cdn.sos.ca.gov/ca-roster/2026/state-agencies.pdf) |
| G–L | [ca-roster/g-l.md](ca-roster/g-l.md) | Same roster |
| M–R | [ca-roster/m-r.md](ca-roster/m-r.md) | Same roster |
| S–Z | [ca-roster/s-z.md](ca-roster/s-z.md) | Same roster |

The other states use the same rule, one file per block:

| States | File |
| --- | --- |
| Alabama through Delaware | [state-agencies/al-de.md](state-agencies/al-de.md) |
| Florida through Kansas | [state-agencies/fl-ks.md](state-agencies/fl-ks.md) |
| Kentucky through Mississippi | [state-agencies/ky-ms.md](state-agencies/ky-ms.md) |
| Missouri through New York | [state-agencies/mo-ny.md](state-agencies/mo-ny.md) |
| North Carolina through South Carolina | [state-agencies/nc-sc.md](state-agencies/nc-sc.md) |
| South Dakota through Wyoming | [state-agencies/sd-wy.md](state-agencies/sd-wy.md) |

A shared function, such as agriculture, is not a rename of those offices. It is recorded only after the printed names are in these files. The enum that points many titles at one function comes after the directories, and it stores the string the state printed.
