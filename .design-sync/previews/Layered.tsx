import { Layered, Reader } from 'lawlibrary-reader'

import { cutSpans, words } from './_data'

const every = ['note', 'clause', 'canon', 'needle', 'mention', 'relation', 'abbreviation']
const all = {
  layers: every,
  layer: (name: string) => every.includes(name),
  kind: () => true,
  has: (layer: string) => every.includes(layer),
}
const act = { toggleLayer() {}, toggleKind() {}, onlyKind() {} }

/**
 * Every reading at once. `Except as provided` is a note, a clause, and a canon
 * over three different lengths of the same phrase, so all three are drawn.
 */
export const EveryReading = () => (
  <Reader shown={all} act={act}>
    <article className="reading">
      <Layered spans={cutSpans} text={words} code="CIV" path="0.0" />
    </article>
  </Reader>
)

/** The citations alone. A span that names a section opens it. */
export const CitationsOnly = () => (
  <Reader shown={all} act={act}>
    <article className="reading">
      <Layered
        spans={cutSpans.filter((span) => span.kind === 'citation' || span.kind === 'cross_reference')}
        text={words}
        code="CIV"
        path="0.0"
      />
    </article>
  </Reader>
)

/** No reading recorded over these words. */
export const NothingRecorded = () => (
  <Reader>
    <article className="reading">
      <Layered spans={[]} text={words} code="CIV" path="0.0" />
    </article>
  </Reader>
)
