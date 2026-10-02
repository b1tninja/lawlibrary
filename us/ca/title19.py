"""Title 19 of the California Code of Regulations, Public Safety.

Division 1 is the State Fire Marshal's own regulations, adopted under the
Administrative Procedure Act rather than through the Building Standards
Commission. Chapter 5 (Automatic Fire Extinguishing Systems) rests on
Health and Safety Code section 13195. Its section 901 incorporates NFPA 25,
2011 edition, by reference, with the Office of the State Fire Marshal's
amendments written into section 901 itself; NFPA and the State Fire Marshal
call the result "NFPA 25, 2013 California Edition". Section 904 sets the
inspection, testing and maintenance duties that follow from it.

There is no text edition here. The Office of Administrative Law's official
CCR is served by Westlaw, which is not a source. The State Fire Marshal's
final-text PDF of the 2014 rulemaking is a strikeout-and-underline record:
its OCR cannot tell deleted words from added ones. Public.Resource.Org's
Title 19 scan (``gov.ca.ccr.19``) is from 2008, before that rulemaking.
The California Fire Code reprints some Division 1 subsections, marked
``[California Code of Regulations, Title 19, Division 1, §...]``; those
reprints are read with the Fire Code.

What is recorded is the adoption: which NFPA 25 edition Title 19 names,
since when. Its effective date is the operative date in the section's
history note (Register 2014, No. 35).
"""

import datetime

from adoption import Adoption, Standard

CITATION = '19 CCR 901'
FINAL_TEXT = (
    'https://34c031f8-c9fd-4018-8c5a-4159cdff6b0d-cdn-endpoint.azureedge.net/-/media/osfm-website/'
    'what-we-do/code-development-and-analysis/title-19-development/'
    'finaltextofregs-nfpa25-2011_8-27-2014corrected_resubfinal.pdf'
)

NFPA_25 = Adoption(
    adopter=CITATION,
    standard=Standard(
        'NFPA', '25', '2011',
        'Standard for the Inspection, Testing, and Maintenance of Water-Based Fire Protection Systems',
    ),
    amended=True,
    effective=datetime.date(2014, 8, 28),
    through=None,
    via=('901', '904'),
    authority=('HSC 13195',),
    source=FINAL_TEXT,
)

ADOPTIONS = (NFPA_25,)
