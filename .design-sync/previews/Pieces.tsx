import { Pieces, Reader } from 'lawlibrary-reader'

import { pieces } from './_data'

/** Subdivision (a) of Civil Code 1940, each annotation wrapped. */
export const AnnotatedText = () => (
  <Reader>
    <article className="reading">
      <Pieces pieces={pieces} code="CIV" />
    </article>
  </Reader>
)

/** Words the index stored with nothing marked on them. */
export const PlainWords = () => (
  <Reader>
    <article className="reading">
      <Pieces text="The holder of an easement shall maintain it in repair." code="CIV" />
    </article>
  </Reader>
)
