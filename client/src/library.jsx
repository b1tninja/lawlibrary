/* The library, one level at a time. `/tree/{url}` is the node; `contents` is
 * the next headings as links. Asked with `expand=all`, `tree` is every
 * heading under the node, nested the way the publisher nests them — the
 * Legislature's expanded table of contents. A section is its own view.
 */

import { useMemo, useState } from 'react'

import { useJson } from './api.js'
import { Link, Pieces } from './marks.jsx'
import { headings, sift } from './outline.js'
import { reasonWords } from './place.js'

export function Crumbs({ crumbs, go }) {
  if (!crumbs || !crumbs.length) return null
  return (
    <nav className="crumbs" aria-label="Breadcrumb">
      <ol>
        {crumbs.map((crumb, index) => (
          <li key={crumb.href + index} className={`cut-${crumb.unit}`}>
            {index === crumbs.length - 1
              ? <span aria-current="page">{crumb.label}</span>
              : <Link href={crumb.href} go={go} title={crumb.label}>{crumb.label}</Link>}
          </li>
        ))}
      </ol>
    </nav>
  )
}

const UNITS = {
  division: 'Division', title: 'Title', part: 'Part',
  chapter: 'Chapter', article: 'Article', section: 'Section',
}


/* A rung the index has no caption for is a bare number, and a list of bare
 * numbers says nothing about what it opens. Name the rung at least. */
function words(item, short) {
  if (short && item.short) return item.short
  if (item.pieces) return <Pieces pieces={item.pieces} />
  const unit = UNITS[item.unit]
  if (unit && item.short && item.label === item.short) return `${unit} ${item.label}`
  return item.label
}

/* How much law is under a rung. The span is only given where the caption does
 * not already carry one. */
function tally(item) {
  if (!item.sections) return ''
  const many = `${item.sections} section${item.sections === 1 ? '' : 's'}`
  return item.first ? `§§ ${item.first}–${item.last} · ${many}` : many
}

/* A rung that holds sections is one a reader can open to the law itself. */
function holds(item) {
  if (!item.holds) return null
  return <span className="holds" title="Holds sections" aria-label="Holds sections">§</span>
}

/* One list of rungs. A rung with rungs under it draws them as its own list,
 * so the nesting on the page is the publisher's and not a margin per unit. */
function Rungs({ items, go, short, nested }) {
  return (
    <ol className={nested ? 'contents nested' : 'contents'}>
      {items.map((item, index) => (
        <li key={item.href + index} className={`cut-${item.unit}`} title={item.label}>
          {item.current
            ? <span aria-current="page">{words(item, short)}</span>
            : <Link href={item.href} go={go}>{words(item, short)}</Link>}
          {holds(item)}
          {tally(item) ? <span className="tally">{tally(item)}</span> : null}
          {item.children && item.children.length
            ? <Rungs items={item.children} go={go} short={short} nested />
            : null}
        </li>
      ))}
    </ol>
  )
}

export function Contents({ items, go, heading, sift: sifts, short, nested, aside }) {
  const [only, setOnly] = useState('')
  const kept = useMemo(() => sift(items, only), [items, only])
  if (!items || !items.length) return null
  const count = nested ? headings(items) : items.length
  return (
    <section className="contents-block">
      <h2>
        {heading || 'Contents'}
        <span className="thin"> {count}</span>
        {aside}
      </h2>
      {sifts && count > 12 ? (
        <p className="sift">
          <input
            value={only}
            placeholder="sift these headings"
            aria-label="Sift the contents"
            onChange={(event) => setOnly(event.target.value)}
          />
        </p>
      ) : null}
      <Rungs items={kept} go={go} short={short} nested={nested} />
      {!kept.length ? <p className="thin">No heading matches that.</p> : null}
    </section>
  )
}

export function Library({ url, go }) {
  const [whole, setWhole] = useState(false)
  const node = '/tree/' + String(url || '').split('/').filter(Boolean).map(encodeURIComponent).join('/')
  const { body, loading } = useJson(whole ? node + '?expand=all' : node)
  if (loading && !body) return <p className="thin">Opening the library.</p>
  if (!body) return null
  if (!body.found) return <p className="miss">{reasonWords(body)}</p>
  const crumbs = body.crumbs || []
  const here = crumbs.length ? crumbs[crumbs.length - 1].label : 'Library'
  // The whole table of contents is drawn from the publisher's tree, which an
  // index built before the trail was stored does not carry. That index
  // answers without `trail`, and then there is nothing to expand.
  const treed = 'trail' in body && (body.contents || []).some((item) => item.unit !== 'section')
  const expanded = whole && Array.isArray(body.tree)
  const toggle = treed ? (
    <button type="button" className="plain expand" onClick={() => setWhole(!whole)}>
      {whole ? 'one level' : 'expand all'}
    </button>
  ) : null
  return (
    <>
      <Crumbs crumbs={crumbs} go={go} />
      <h1>{here}</h1>
      <p className="beside">
        <span className="thin">{body.url || 'us-ca'}</span>
        {body.code ? (
          <a className="plain" href={`/mirror/${body.url}`}>reference copy</a>
        ) : null}
      </p>
      {expanded
        ? <Contents items={body.tree} go={go} sift nested heading="Contents" aside={toggle} />
        : <Contents items={body.contents} go={go} sift heading="Contents" aside={toggle} />}
      {!(body.contents || []).length ? <p className="thin">No further headings.</p> : null}
    </>
  )
}
