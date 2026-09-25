# Canons of construction

These notes are for the lexical pass. A canon tells a reader how to treat words that are already in the text. The lexer finds the words. When one sentence supports two canons that disagree, `ambiguities` reports both readings and stops. It does not decide the case.

Each file has twenty entries. An entry names the canon, says what a reader is supposed to do, and gives a short illustration. Illustrations are patterns, not quotations of a code or an opinion.

| File | What it covers |
| --- | --- |
| [textual.md](textual.md) | Ordinary meaning, associated words, *ejusdem generis*, *expressio unius*, surplusage, consistent usage, last antecedent, *shall* and *may* |
| [structural.md](structural.md) | Enacting clause, titles, findings, definitions, proviso, savings, severability, effective date, sunset, repealer, and which of those `lexical.py` already marks |
| [substantive.md](substantive.md) | Avoidance, lenity, retroactivity, extraterritoriality, clear-statement rules, and *Chevron* as overruled by *Loper Bright* |
| [classical.md](classical.md) | Literal, golden, and mischief rules, and *lex posterior*, *lex specialis*, and *lex superior* |

The clause search itself is `lexical.py`. The libraries that can supply a sentence grammar later are [libraries.md](../libraries.md). Drafting idioms are in [idioms.md](../idioms.md). Maxims that are not one of these eighty entries are in [maxims.md](../maxims.md). Citation shapes taken from official manuals are in [style.md](../style.md). How a reference is stored for lookup is in [references.md](../references.md). A few sections can be drawn from one book with [sample.md](../sample.md).
