import { Cuts } from 'lawlibrary-reader'

import { spans, tree } from './_data'

/** Civil Code 1940 as the cuts under it, every reading drawn over the words. */
export const ASection = () => <Cuts tree={tree} code="CIV" spans={spans} />

/** One subdivision with the annotations alone, before the layers arrive. */
export const WithoutTheLayers = () => <Cuts tree={tree.children[0]} code="CIV" />

/** A subdivision and the paragraphs and subparagraphs inside it. */
export const OneSubdivision = () => (
  <Cuts tree={tree.children[1]} code="CIV" spans={spans} />
)
