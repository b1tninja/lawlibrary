/* The closure. Each unit remembers the one above it, the way
 * `division(1).part('2.52')` does, and the server prints the citation that
 * place makes. `use` picks read, find, refs, or gaps.
 */

import { useEffect, useState } from 'react'

import { route, useJson } from './api.js'
import { Graph } from './graph.jsx'
import { Hits } from './find.jsx'
import { Link } from './marks.jsx'
import {
  CLOSURE_UNITS, closureHref, graphHref, reasonWords, sectionHref,
} from './place.js'

const USES = [
  ['read', 'read the section'],
  ['find', 'find words inside'],
  ['refs', 'walk the citations'],
  ['gaps', 'check the citations'],
]

const HOPS = [['0', 'this section'], ['1', 'one hop'], ['2', 'two hops'], ['all', 'until a repeat']]

function Filters({ asked, change, codes, sessions, go }) {
  return (
    <form
      className="find wide closure"
      onSubmit={(event) => {
        event.preventDefault()
        go(event, closureHref(asked))
      }}
    >
      <label>
        Book
        <select value={asked.code || ''} onChange={(event) => change('code', event.target.value)}>
          <option value="">name a book</option>
          {codes.map((row) => <option key={row.code} value={row.code}>{row.title}</option>)}
        </select>
      </label>
      {CLOSURE_UNITS.map((unit) => (
        <label key={unit}>
          {unit}
          <input
            size="6"
            value={asked[unit] || ''}
            onChange={(event) => change(unit, event.target.value)}
          />
        </label>
      ))}
      <label>
        Use
        <select value={asked.use || ''} onChange={(event) => change('use', event.target.value)}>
          <option value="">follow the filters</option>
          {USES.map(([value, words]) => <option key={value} value={value}>{words}</option>)}
        </select>
      </label>
      <label>
        Words
        <input value={asked.q || ''} onChange={(event) => change('q', event.target.value)} />
      </label>
      <label>
        Walk
        <select value={asked.hops || ''} onChange={(event) => change('hops', event.target.value)}>
          <option value="">once</option>
          {HOPS.map(([value, words]) => <option key={value} value={value}>{words}</option>)}
        </select>
      </label>
      <label>
        Only
        <input
          size="10"
          placeholder="CIV,INS"
          value={asked.only || ''}
          onChange={(event) => change('only', event.target.value)}
        />
      </label>
      <label>
        Year
        <select value={asked.session || ''} onChange={(event) => change('session', event.target.value)}>
          <option value="">current</option>
          {sessions.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
      </label>
      <label className="flag">
        <input
          type="checkbox"
          checked={Boolean(asked.same)}
          onChange={(event) => change('same', event.target.checked ? '1' : '')}
        />
        stay in this book
      </label>
      <button>Open</button>
    </form>
  )
}

export function Closure({ here, codes, sessions, go }) {
  const [asked, setAsked] = useState(here)
  useEffect(() => { setAsked(here) }, [here])
  const sent = {}
  Object.keys(here).forEach((name) => {
    if (name !== 'kind' && here[name]) sent[name] = here[name]
  })
  const url = here.code ? route('/closure', sent) : ''
  const { body, loading } = useJson(url)
  function change(name, value) {
    setAsked((was) => ({ ...was, [name]: value }))
  }
  const filters = (body && body.filters) || null
  return (
    <>
      <h1>A closure</h1>
      <Filters asked={asked} change={change} codes={codes} sessions={sessions} go={go} />
      {!here.code ? (
        <p className="thin">
          Name a book. A unit remembers the unit above it, and the reference below is the
          citation that place prints.
        </p>
      ) : null}
      {loading && !body ? <p className="thin">Opening.</p> : null}
      {body && !body.found ? <p className="miss">{reasonWords(body)}</p> : null}
      {filters ? (
        <p className="reference">
          <span className="thin">{filters.use}</span>
          <strong>{filters.reference}</strong>
        </p>
      ) : null}
      {body && body.found && body.section && body.section.found ? (
        <p className="beside">
          <Link href={sectionHref(body.section.code, body.section.section, { session: here.session })} go={go}>
            {`open ${body.section.citation}`}
          </Link>
          <span className="thin">{`${(body.section.text || '').split(/\s+/).length} words`}</span>
        </p>
      ) : null}
      {body && body.found && body.section && body.section.found ? (
        <article className="reading plain-words">{body.section.text}</article>
      ) : null}
      {body && body.hits ? <Hits hits={body.hits} go={go} /> : null}
      {body && body.edges ? (
        <Graph
          edges={body.edges}
          nodes={body.nodes}
          go={go}
          here={`${here.code} ${here.section}`}
          empty="That place names no statute the index holds."
        />
      ) : null}
      {body && body.gaps ? (
        (body.gaps || []).length ? (
          <ol className="refs">
            {body.gaps.map((gap, index) => (
              <li key={index} className={`gap-${gap.gap}`}>
                <span className="ref-source">{String(gap.gap).replace(/_/g, ' ')}</span>
                <span>{gap.phrase}</span>
                {gap.href ? <Link href={gap.href} go={go}>{gap.citation}</Link> : null}
              </li>
            ))}
          </ol>
        ) : <p className="thin">Every citation in those words was recorded.</p>
      ) : null}
    </>
  )
}

/* One section's walk, on its own page, so the drawing has the width. */
export function GraphView({ here, go }) {
  const url = here.code && here.section
    ? route('/closure', {
      code: here.code,
      section: here.section,
      use: 'refs',
      hops: here.hops || '1',
      only: here.only,
      same: here.same,
      session: here.session,
    })
    : ''
  const { body, loading } = useJson(url)
  if (!url) return <p className="thin">Name a book and a section.</p>
  if (loading && !body) return <p className="thin">Walking the citations.</p>
  if (!body) return null
  if (!body.found) return <p className="miss">{reasonWords(body)}</p>
  return (
    <>
      <h1>{`${here.code} ${here.section}`}</h1>
      <p className="beside">
        <Link href={sectionHref(here.code, here.section, { session: here.session })} go={go}>
          read the section
        </Link>
        {HOPS.map(([value, words]) => (
          <Link key={value} href={graphHref({ ...here, hops: value, kind: undefined })} go={go}>
            {(here.hops || '1') === value ? `✓ ${words}` : words}
          </Link>
        ))}
      </p>
      <Graph
        edges={body.edges}
        nodes={body.nodes}
        go={go}
        here={`${here.code} ${here.section}`}
        empty="That section names no statute the index holds."
      />
    </>
  )
}
