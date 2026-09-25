import { Reader, TermCard } from 'lawlibrary-reader'

import { term } from './_data'

const go = () => {}

/** A word looked up: how often it occurs, the words beside it, where else it is. */
export const AWordLookedUp = () => (
  <Reader>
    <TermCard
      looking={{ term: 'dwelling', code: 'CIV' }}
      reply={term}
      go={go}
      pinned
    />
  </Reader>
)

/**
 * A canon. The reading is the one the record already carries, so the card
 * teaches what `shall` does rather than restating the word.
 */
export const ACanon = () => (
  <Reader>
    <TermCard
      looking={{
        term: 'shall',
        text: 'shall',
        code: 'CIV',
        layer: 'canon',
        kind: 'mandatory',
        target: 'shall',
        reading: 'The duty is obligatory.',
      }}
      reply={{ found: false }}
      go={go}
      pinned
    />
  </Reader>
)

/** An internal reference, resolved to the heading it means. */
export const AnInternalReference = () => (
  <Reader>
    <TermCard
      looking={{
        term: 'this chapter',
        text: 'this chapter',
        code: 'CIV',
        layer: 'note',
        kind: 'cross_reference',
        target: 'CIV this chapter',
        href: '/view/tree/us-ca/civ/division/3/title/5/part/4/chapter/2',
        detail: { resolved: 'CHAPTER 2. Hiring of Real Property [1940. - 1954.1.]' },
      }}
      reply={{ found: false }}
      go={go}
      pinned
    />
  </Reader>
)
