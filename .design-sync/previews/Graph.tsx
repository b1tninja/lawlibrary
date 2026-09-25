import { Graph } from 'lawlibrary-reader'

import { bookEdges, walkEdges, walkNodes } from './_data'

const go = () => {}

/** Two hops out of Civil Code 1940. A dashed node was named but not opened. */
export const AWalk = () => (
  <Graph edges={walkEdges} nodes={walkNodes} go={go} here="CIV 1940" />
)

/** Which book cites which. Hundreds of edges read as a grid, not a hairball. */
export const BookToBook = () => <Graph edges={bookEdges} go={go} />

/** Nothing stored for that section. */
export const NothingStored = () => (
  <Graph edges={[]} go={go} empty="This section names no statute the index holds." />
)
