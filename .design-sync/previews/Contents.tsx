import { Contents, Reader } from 'lawlibrary-reader'

import { contents } from './_data'

const go = () => {}

/** The sections beside Civil Code 1940, the open one marked. */
export const BesideThisSection = () => (
  <Reader>
    <Contents items={contents} go={go} heading="Beside it" short sift />
  </Reader>
)

/** The same list with each section's full caption. */
export const WithTheCaptions = () => (
  <Reader>
    <Contents items={contents.slice(0, 5)} go={go} heading="Contents" />
  </Reader>
)
