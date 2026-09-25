import { Formats, Reader } from 'lawlibrary-reader'

import { formats } from './_data'

/** The same section under every representation the library serves. */
export const EveryRepresentation = () => (
  <Reader>
    <Formats formats={formats} />
  </Reader>
)

/** The two a reader asks for most. */
export const TextAndMarkdown = () => (
  <Reader>
    <Formats formats={formats.filter((row) => row.hint === 'txt' || row.hint === 'md')} />
  </Reader>
)
