import { Crumbs } from 'lawlibrary-reader'

import { crumbs } from './_data'

const go = () => {}

/** A section, from the library down to the section sign. */
export const AboveASection = () => <Crumbs crumbs={crumbs} go={go} />

/** A book, before any heading has been opened. */
export const AboveABook = () => <Crumbs crumbs={crumbs.slice(0, 4)} go={go} />

/** The shortest trail there is: the library, and where you are. */
export const AtTheRegion = () => <Crumbs crumbs={crumbs.slice(0, 3)} go={go} />
