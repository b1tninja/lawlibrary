/* The library, one level at a time. `/tree/{url}` is the node; `contents` is
 * the next headings as links. A section is its own view.
 */

import { useMemo, useState } from 'react'

import { useJson } from './api.js'
import { Link, Pieces } from './marks.jsx'
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

export function Contents({ items, go, heading, sift, short }) {
  const [only, setOnly] = useState('')
  const kept = useMemo(() => {
    const needle = only.trim().toLowerCase()
    if (!needle) return items || []
    return (items || []).filter((item) => String(item.label || '').toLowerCase().includes(needle))
  }, [items, only])
  if (!items || !items.length) return null
  return (
    <section className="contents-block">
      <h2>
        {heading || 'Contents'}
        <span className="thin"> {items.length}</span>
      </h2>
      {sift && items.length > 12 ? (
        <p className="sift">
          <input
            value={only}
            placeholder="sift these headings"
            aria-label="Sift the contents"
            onChange={(event) => setOnly(event.target.value)}
          />
        </p>
      ) : null}
      <ol className="contents">
        {kept.map((item, index) => (
          <li key={item.href + index} className={`cut-${item.unit}`} title={item.label}>
            {item.current
              ? <span aria-current="page">{words(item, short)}</span>
              : <Link href={item.href} go={go}>{words(item, short)}</Link>}
            {tally(item) ? <span className="tally">{tally(item)}</span> : null}
          </li>
        ))}
      </ol>
      {!kept.length ? <p className="thin">No heading matches that.</p> : null}
    </section>
  )
}

export function Library({ url, go }) {
  const { body, loading } = useJson('/tree/' + String(url || '').split('/').filter(Boolean).map(encodeURIComponent).join('/'))
  if (loading && !body) return <p className="thin">Opening the library.</p>
  if (!body) return null
  if (!body.found) return <p className="miss">{reasonWords(body)}</p>
  const crumbs = body.crumbs || []
  const here = crumbs.length ? crumbs[crumbs.length - 1].label : 'Library'
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
      <Contents items={body.contents} go={go} sift heading="Contents" />
      {!(body.contents || []).length ? <p className="thin">No further headings.</p> : null}
    </>
  )
}
