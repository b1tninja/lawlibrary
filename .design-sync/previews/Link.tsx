import { Link, Reader } from 'lawlibrary-reader'

const go = () => {}

/** A section the words named. A `/view` path opens the same place in the reader. */
export const ToASection = () => (
  <Reader>
    <p>
      <Link href="/view/section/RTC/7280" go={go}>RTC 7280</Link>
    </p>
  </Reader>
)

/** A heading in the tree. */
export const ToAHeading = () => (
  <Reader>
    <p>
      <Link href="/view/tree/us-ca/civ/division/3" go={go}>
        DIVISION 3. OBLIGATIONS [1427. - 3272.9.]
      </Link>
    </p>
  </Reader>
)

/** A link that carries its own words, with the citation as its title. */
export const InASentence = () => (
  <Reader>
    <article className="reading">
      Occupancy subject to tax under{' '}
      <Link href="/view/section/RTC/7280" go={go} title="RTC 7280">
        Section 7280 of the Revenue and Taxation Code
      </Link>
      .
    </article>
  </Reader>
)
