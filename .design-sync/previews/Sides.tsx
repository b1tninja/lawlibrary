import { Reader, Sides } from 'lawlibrary-reader'

import { contents } from './_data'

const go = () => {}

/** The sections on either side, inside the tightest heading. */
export const BothSides = () => (
  <Reader>
    <Sides code="CIV" previous="1939.5" next="1940.1" go={go} />
  </Reader>
)

/** The first section of a chapter: nothing before it. */
export const FirstInTheChapter = () => (
  <Reader>
    <Sides code="CIV" next={String(contents[1].short)} go={go} />
  </Reader>
)

/** The last section of a chapter. */
export const LastInTheChapter = () => (
  <Reader>
    <Sides code="CIV" previous="1954.06" go={go} />
  </Reader>
)
