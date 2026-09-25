import { Hits, Reader } from 'lawlibrary-reader'

import { hits } from './_data'

const go = () => {}

/** What the index returned for "habitability". */
export const WhatSearchOpened = () => (
  <Reader>
    <Hits hits={hits} go={go} />
  </Reader>
)

/** One section, with the heading path above the words. */
export const OneSection = () => (
  <Reader>
    <Hits hits={hits.slice(0, 1)} go={go} />
  </Reader>
)

/** A phrase no section carries. */
export const NoMatch = () => (
  <Reader>
    <Hits hits={[]} go={go} />
  </Reader>
)
