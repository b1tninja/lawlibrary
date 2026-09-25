# How an office is enacted

The roster prints a name. The statute often prints that name in another order, and it uses a few frames to create the office. `name_queries` turns a roster line into the phrases worth searching. `find_enactments` marks the frames. `hunt_authorities` runs those phrases against the California index and keeps a hit only when a frame is in the snippet.

Known offices stay the search keys. The frames are what the hunt looks for, so a new department does not need its own pattern.

| Frame | Words | What it pins |
| --- | --- | --- |
| Establishment | “There is in … a Department / Board / Bureau / Office / Commission / Agency” | The office and the body it sits in |
| Officer | “the chief officer of which … is named” | The title of the person who heads it |
| Creation | “There is hereby created” or “hereby established” | A body created in that section |
| Continuation | “is continued in existence” | An office an earlier statute already created |
| Vesting | “powers and duties … are vested in” | Who received the office’s duties |

## What the index returned

Business and Professions Code section 10050, read from the local index:

> There is in the Business and Transportation Agency a Department of Real Estate, the chief officer of which department is named the Real Estate Commissioner.

That is both an establishment frame and an officer frame. The roster name is `Real Estate, Department of (DRE)`. The statute says `Department of Real Estate`. `CaliforniaDepartmentOfRealEstate.authority` is `BPC 10050`.

The same establishment frame creates other offices. Education Code section 33300: “There is in the state government a State Department of Education.” Education Code section 33000 uses it for the State Board of Education. Education Code section 94875 continues the Bureau for Private Postsecondary Education: “is continued in existence.”

A superior court is not created by that department frame. California Constitution article VI, section 4 is the establishment: one superior court in each county. The hunt for a court still starts from the court registered in `court.py`, then looks for “superior court” plus the county name.

Offices registered under another state are not in the California index. The hunt skips a parent that is not a region code, and a region with no rows simply returns no pins.

## Duties and relationships

Creating the office is not the same as saying what it must do. `find_relations` marks the second kind of phrase. The words below are the ones in Business and Professions Code sections 10050, 10071, and 10080.

| Relation | Words | What it pins |
| --- | --- | --- |
| `responsibility` | “principal responsibility of … to” | The office’s main charge. Section 10050: the commissioner’s principal responsibility is to enforce the real-estate licensing laws |
| `duty` | “shall enforce the provisions” or “acts and duties” | A command the officer must carry out. Section 10071 |
| `power` | “full power to” or “may adopt, amend, or repeal” | Authority the officer may use. Section 10071 regulates licenses. Section 10080 adopts rules |
| `procedure` | “in accordance with the provisions of the Administrative Procedure” | The other statute the duty has to follow. Section 10080 points at the California Administrative Procedure Act |
| `scope` | “commencing with Section” plus a number | The span of code the duty covers. Section 10050 names the part that begins at section 10000 |
| `appointment` | “appointed by the Governor” | Who fills the office |
| `supervision` | “under the supervision of” | The body the office answers to |

A pin from `hunt_authorities` now lists both `frames` and `relations` when the section text contains them.
