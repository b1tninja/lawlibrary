# Maxims and brocards (beyond the eighty canons)

The eighty canons of construction live in [canons/](canons/). They cover textual list rules, structural clause layout, substantive presumptions, and the classical conflict trio (*lex posterior*, *lex specialis*, *lex superior*). This file is the residue a statutory lexer still needs: Latin brocards and equity formulas that are **not** already named as entries there.

Do not duplicate [textual.md](canons/textual.md) (*noscitur*, *ejusdem generis*, *expressio unius*, surplusage, general/specific), [structural.md](canons/structural.md) (*in pari materia*), or [classical.md](canons/classical.md) (*reddendo singula singulis*, *generalia specialibus non derogant*, *lex specialis*). *Contemporanea expositio* gets a full row here because the textual file only pairs the Latin name with the fixed-meaning canon.

## Discipline (`canons.py`)

`canons.find_signals` marks every phrase that supports a reading. When two canons in the same sentence pull apart, `canons.ambiguities` returns both. The marker does not choose. A period starts a new sentence. The same discipline applies to the maxims below: record the candidate; do not pick a winner.

## How to use this list

For each maxim: English name, Latin name, what the reader does, whether a lexer can see it in wording, words to watch, and a short labeled illustration (a pattern, not a holding). Where the local California index returned a maxim already written into Civil Code Part 4 (Maxims of Jurisprudence), one retrieved sentence is quoted and cited. Civil Code section 3509 states that those maxims aid application and do not qualify the rest of the Code; treat them as interpretive vocabulary, not operative duties.

---

## 1. Casus omissus

**Latin:** *casus omissus* (“the omitted case”).

**Do:** Do not invent coverage for a case the statute never names. Silence is omission, not a blank to fill with analogous duties or rights.

**Lexer-visible:** no (absence of words). Soft yes when the text itself flags a gap (“not provided for,” “omitted,” “except as otherwise provided” with no matching provision).

**Words to watch:** `omitted`, `not provided for`, `silent as to`, closed enumerations with no residual class; contrast with `including` / `or other` (those invite other canons, not gap-filling).

**Illustration (pattern):** A fee schedule that lists three filing types and says nothing about a fourth does not, under *casus omissus*, grow a fourth rate by analogy.

---

## 2. Expressum facit cessare tacitum

**Latin:** *expressum facit cessare tacitum* (“what is expressed makes what is silent cease”).

**Do:** When the statute speaks expressly on a point, do not imply a conflicting silent rule beside it. Expression stops implication on the same subject.

**Lexer-visible:** yes, when express clauses sit next to silence that a reader might fill.

**Words to watch:** `expressly`, `only`, `shall` / `may` that name one procedure; `nothing in this … shall be construed to`; contrast with bare omission (*casus omissus*) and with *expressio unius* (already in textual canons).

**Illustration (pattern):** A section that “expressly” authorizes one form of notice is not read to authorize a second form by implication.

**Distinct from:** *expressio unius* (naming items in a set implies exclusion of unmentioned items). This maxim is about express text cutting off implied side-rules, not about closed lists alone.

---

## 3. Lex nil frustra

**Latin:** *lex nil frustra facit* / *lex nihil frustra facit* (“the law does nothing in vain”).

**Do:** Prefer a reading under which the enactment does real work. Do not treat a whole provision as idle theater if another fair reading gives it effect.

**Lexer-visible:** partial. Paired idle-looking phrases are visible; futility of an entire scheme is a later judgment.

**Words to watch:** `each and every`, `null and void`, `force and effect`, `shall have effect`, `for the purposes of`; dual requirements that would collapse under a narrower reading.

**Illustration (pattern):** A clause that both creates a board and assigns it a duty is not read so the board exists with nothing to do, if the words support a working duty.

**Index:** Civil Code section 3532 — “The law neither does nor requires idle acts.”

**Distinct from:** the anti-surplusage canon (every *word* does work). This maxim asks whether the *law* is presumed futile.

---

## 4. Contemporanea expositio

**Latin:** *contemporanea expositio est optima et fortissima in lege* (“contemporaneous exposition is the best and strongest in law”).

**Do:** Early practical reading of the words—near the time of enactment—carries weight when later usage has drifted. Aligns with the fixed-meaning canon in [textual.md](canons/textual.md); this row is the Latin brocard and its drafting cue.

**Lexer-visible:** no for historical practice itself. Yes for enactment-era definitional frames still in the text.

**Words to watch:** `as used in this Act`, `means`, effective-date and enactment cues; do not treat modern slang synonyms as if they were in the original wording.

**Illustration (pattern):** A word that named one class of device at enactment is not stretched to a later invention that only shares a modern nickname.

**Index:** Civil Code section 3535 — “Contemporaneous exposition is in general the best.”

---

## 5. Ut res magis valeat quam pereat

**Latin:** *ut res magis valeat quam pereat* (“so that the thing may rather have effect than perish”).

**Do:** Among fair readings, prefer the one that keeps the provision alive and operative over the one that nullifies it.

**Lexer-visible:** partial. Tension between a voiding reading and a saving reading can be flagged; the choice is not the lexer’s.

**Words to watch:** `shall be void`, `of no effect`, `invalid`, `severable`, `to the extent`; savings and severability formulas (see structural canons).

**Illustration (pattern):** If one reading of a licensing sentence would make every license in the chapter fail, and another reading lets licenses stand, mark both and prefer the effective reading only at the reasoner stage.

**Index:** Civil Code section 3541 — “An interpretation which gives effect is preferred to one which makes void.”

---

## 6. Lex non cogit ad impossibilia

**Latin:** *lex non cogit ad impossibilia* (“the law does not compel the impossible”).

**Do:** Do not read a duty so that compliance is impossible on the face of the words and the world the statute assumes.

**Lexer-visible:** rare. Visible when the text itself uses impossibility language; otherwise a later reasoner flags absurd duty pairs.

**Words to watch:** `impossible`, `impracticable`, `unable to`, deadlines that cannot both be met, duties that cancel each other in one sentence.

**Illustration (pattern):** A rule that requires a filing “before the event that creates the duty to file” is marked for impossibility review.

**Index:** Civil Code section 3531 — “The law never requires impossibilities.”

**Related:** golden-rule / absurdity tension in the classical and substantive canon files; do not treat this maxim as a free rewrite.

---

## 7. Cessante ratione legis

**Latin:** *cessante ratione legis, cessat et ipsa lex* (“when the reason of the law ceases, the law itself ceases”).

**Do:** If the stated reason for a rule is gone, the rule’s application may fall with it—only where the forum still accepts this older maxim, and never against clear prospective text that still speaks.

**Lexer-visible:** yes when the statute recites its reason; no when the “reason” is supplied from outside the text.

**Words to watch:** `because`, `whereas`, `the purpose of`, `no longer`, sunset and temporary clauses; purpose and findings spans (structural canons).

**Illustration (pattern):** A wartime price rule tied to “for the duration of the emergency” is a candidate for *cessante* once the emergency clause ends—by the words, not by outside narrative alone.

**Index:** Civil Code section 3510 — “When the reason of a rule ceases, so should the rule itself.”

---

## 8. Omne majus continet in se minus

**Latin:** *omne majus continet in se minus* (“the greater contains the less”).

**Do:** Authority or a grant stated at a higher level is presumed to include the lesser powers or quantities needed to carry it out, unless the text withholds them.

**Lexer-visible:** partial. Visible in nested grants (“any,” “all,” “including the power to”); the inclusion judgment is not automatic.

**Words to watch:** `any`, `all`, `full power`, `necessary`, `incidental`, `including`; nested fee or penalty schedules.

**Illustration (pattern):** A grant of power “to regulate the trade” can be read to include lesser steps named nowhere if the forum still uses this maxim—and must be marked as a candidate, not as a holding.

**Index:** Civil Code section 3536 — “The greater contains the less.”

---

## 9. De minimis non curat lex

**Latin:** *de minimis non curat lex* (“the law does not concern itself with trifles”).

**Do:** Trivial departures are disregarded when the statute’s scale makes them noise, unless the text makes every unit matter (zero-tolerance wording).

**Lexer-visible:** yes when the text sets thresholds, tolerances, or “approximate” measures; no when “trifle” is only a litigation argument.

**Words to watch:** `approximately`, `more or less`, `de minimis`, `trifling`, `nominal`, numeric floors and safe harbors.

**Illustration (pattern):** A weight limit of “not more than 100 pounds” is not ordinarily broken by a scale’s half-ounce jitter unless the statute says exact weight controls.

**Index:** Civil Code section 3533 — “The law disregards trifles.”

---

## 10. Superfluity does not vitiate

**Latin:** *superflua non nocent*; often paired with *falsa demonstratio non nocet* (“a false description does not hurt”) and with *abundans cautela non nocet* (“abundant caution does no harm”).

**Do:** Extra or mistaken descriptive words do not destroy an otherwise clear identification or grant. Surplus caution in drafting is not a separate operative limit.

**Lexer-visible:** yes for piled descriptors and “for the avoidance of doubt” caution phrases.

**Words to watch:** `for the avoidance of doubt`, `without prejudice to`, `for the sake of clarity`, `also known as`, surplus parentheticals after a clear name or cite.

**Illustration (pattern):** “the Alpha Bridge (also called the Old Town span)” still points at Alpha Bridge if the parenthetical nickname is wrong.

**Index:** Civil Code section 3537 — “Superfluity does not vitiate.”

**Distinct from:** anti-surplusage (prefer a reading that *uses* every word). Here the maxim saves the instrument when extra words are wrong or idle.

---

## 11. Ex abundanti cautela (drafting habit)

**Latin:** *ex abundanti cautela* (“from an abundance of caution”).

**Do:** Treat cautionary restatements as insurance for the drafter, not as a second, narrower rule—unless the cautionary clause uses operative verbs that change the duty.

**Lexer-visible:** yes.

**Words to watch:** `for the avoidance of doubt`, `for greater certainty`, `without limiting the generality of`, `including without limitation`, `nothing in this section limits`.

**Illustration (pattern):** “The board may inspect, and for the avoidance of doubt may photograph, the site” does not shrink “inspect” merely because photography was spelled out.

---

## 12. Ubi jus ibi remedium (not a drafting hook)

**Latin:** *ubi jus ibi remedium* (“where there is a right, there is a remedy”).

**Do:** As case-law doctrine, courts sometimes imply a remedy for a right. For the **statutory lexer**, this is not a hook that creates duties or causes of action from silence.

**Lexer-visible:** no as an implication engine. Yes only if the statute uses the English maxim words.

**Words to watch:** `remedy`, `cause of action`, `shall be entitled to relief` when those are operative; do **not** invent a remedy clause from a bare right-stating sentence.

**Illustration (pattern):** “Each member has a right to inspect the books” is not, for the lexer, rewritten into “and may sue for an injunction.” Remedies stay where the text (or another statute) puts them.

**Index:** Civil Code section 3523 states “For every wrong there is a remedy.” Read with section 3509: the maxim aids application; it does not by itself add a private right of action to every duty in the Code.

---

## 13. No one takes advantage of his own wrong

**Latin:** *nullus commodum capere potest de injuria sua propria* (clean-hands kin).

**Do:** A party does not use the statute to profit from wrongdoing the party caused. Include only because some codes write the equity idea as words; it is not a general invitation to import chancery doctrine.

**Lexer-visible:** yes when the statute uses this English (or close) formula; no as freestanding equity gloss on every duty.

**Words to watch:** `own wrong`, `unclean hands`, `fraudulently`, `shall not benefit from`, forfeiture tied to misconduct.

**Illustration (pattern):** A section that denies a benefit to one who “obtained the license by fraud” is a clean-hands-style drafting pattern, not a warrant to deny every benefit on moral grounds.

**Index:** Civil Code section 3517 — “No one can take advantage of his own wrong.”

**Skip as freestanding doctrine:** “he who seeks equity must do equity” and bare “clean hands” when they appear only in opinions, not in the statute’s words.

---

## 14. He who takes the benefit must bear the burden

**Latin:** *qui sentit commodum sentire debet et onus*.

**Do:** Acceptance of a statutory benefit carries the attached statutory burden when the text pairs them.

**Lexer-visible:** yes when benefit and burden are drafted together.

**Words to watch:** `in consideration of`, `subject to`, `provided that`, paired `entitled` / `shall pay` / `shall comply`.

**Illustration (pattern):** “A licensee is entitled to the privilege and shall maintain the bond” pairs benefit and burden in one scheme.

**Index:** Civil Code section 3521 — “He who takes the benefit must bear the burden.”

---

## 15. Vigilantibus non dormientibus

**Latin:** *vigilantibus non dormientibus jura subveniunt* (“the laws aid the vigilant, not those who sleep on their rights”).

**Do:** Delay and limitations matter. The maxim supports reading time bars and diligence requirements as real, not optional courtesy.

**Lexer-visible:** yes for limitations and diligence words; the equity slogan alone is not a trigger.

**Words to watch:** `within … days`, `statute of limitations`, `laches`, `diligent`, `timely`, `waiver by delay`.

**Illustration (pattern):** A claim period of “90 days after discovery” is read as a real bar, not as advice.

**Index:** Civil Code section 3527 — “The law helps the vigilant, before those who sleep on their rights.”

---

## Count and skips

**15** maxims documented above.

**Deliberately skipped as already named in the canon files:**

| Maxim / brocard | Where it already lives |
| --- | --- |
| *Noscitur a sociis* | textual §§4, 19; classical §18 cross-note |
| *In pari materia* | structural §17 (textual §8 notes the relation) |
| *Reddendo singula singulis* | classical §12 |
| *Generalia specialibus non derogant* | classical §13; textual §11 (general/specific) |
| *Lex specialis derogat legi generali* | classical §8 |
| *Ejusdem generis* / *expressio unius* / surplusage | textual (and classical cross-notes) |
| Particular expressions qualify general (Civ. Code §3534 sense) | same family as general/specific and *generalia specialibus* |
| Retroactivity / *nova constitutio futuris…* | substantive presumption against retroactivity |
| Lenity / *in dubio pro reo* | substantive rule of lenity |
| *Chevron* deference | substantive §8 — **overruled** by *Loper Bright*; historical label only |

The canons that tell a reader how to treat words once found remain [canons/index.md](canons/index.md). Clause strategies for court-creating language are [clauses.md](clauses.md).
