/* Full text, one expression, a heading span, and the stored annotations. */

import { useEffect, useState } from 'react'

import { route, useJson } from './api.js'
import { Link, noteWords } from './marks.jsx'
import {
  annotationsHref, reasonWords, searchHref, sectionHref,
} from './place.js'

function Path({ steps }) {
  if (!steps || !steps.length) return null
  return (
    <span className="hit-path thin">
      {steps.map((step) => step.heading).filter(Boolean).join(' · ')}
    </span>
  )
}

export function Hits({ hits, go }) {
  if (!hits || !hits.length) return <p className="thin">No section matched.</p>
  return (
    <ol className="hits">
      {hits.map((hit, index) => (
        <li key={(hit.href || hit.citation) + index}>
          <p className="hit-head">
            {hit.href
              ? <Link href={hit.href} go={go}>{hit.citation}</Link>
              : <span>{hit.citation}</span>}
            <Path steps={hit.path} />
          </p>
          {hit.snippet ? <p className="hit-words">{hit.snippet}</p> : null}
        </li>
      ))}
    </ol>
  )
}

export function Search({ here, codes, sessions, go }) {
  const [asked, setAsked] = useState(here)
  useEffect(() => { setAsked(here) }, [here])
  const url = here.q
    ? route('/search', {
      q: here.q,
      code: here.code,
      start: here.start,
      end: here.end,
      session: here.session,
      limit: here.limit,
    })
    : ''
  const { body, loading } = useJson(url)
  function change(name, value) {
    setAsked((was) => ({ ...was, [name]: value }))
  }
  return (
    <>
      <h1>{here.q ? `“${here.q}”` : 'Search the index'}</h1>
      <form
        className="find wide"
        onSubmit={(event) => {
          event.preventDefault()
          if (asked.q && asked.q.trim()) go(event, searchHref({ ...asked, kind: undefined }))
        }}
      >
        <label>
          Words
          <input
            value={asked.q || ''}
            autoFocus
            onChange={(event) => change('q', event.target.value)}
          />
        </label>
        <label>
          Book
          <select value={asked.code || ''} onChange={(event) => change('code', event.target.value)}>
            <option value="">every book</option>
            {codes.map((row) => <option key={row.code} value={row.code}>{row.title}</option>)}
          </select>
        </label>
        <label>
          From
          <input
            value={asked.start || ''}
            size="7"
            onChange={(event) => change('start', event.target.value)}
          />
        </label>
        <label>
          To
          <input
            value={asked.end || ''}
            size="7"
            onChange={(event) => change('end', event.target.value)}
          />
        </label>
        <label>
          Year
          <select value={asked.session || ''} onChange={(event) => change('session', event.target.value)}>
            <option value="">current</option>
            <option value="all">every year</option>
            {sessions.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <button>Find</button>
      </form>
      {loading && !body ? <p className="thin">Searching.</p> : null}
      {body && !body.found ? <p className="miss">{reasonWords(body)}</p> : null}
      {body && body.found ? <Hits hits={body.hits} go={go} /> : null}
    </>
  )
}

export function Outline({ body, go, asked }) {
  const nodes = body.nodes || []
  const code = body.code || (asked && asked.code) || ''
  return (
    <>
      <h1>{`${code} ${body.start}–${body.end}`}</h1>
      <p className="beside">
        <span className="thin">{nodes.length} headings</span>
        <Link href={searchHref({ code, start: body.start, end: body.end })} go={go}>
          search inside this span
        </Link>
      </p>
      {body.reason === 'span_too_large' ? (
        <p className="thin">{reasonWords(body)}</p>
      ) : null}
      <ol className="contents">
        {nodes.map((node, index) => (
          <li key={index} className={`cut-${node.level}`}>
            {node.first
              ? (
                <Link href={sectionHref(code, node.first)} go={go}>
                  {node.heading || node.level}
                </Link>
              )
              : <span>{node.heading || node.level}</span>}
            <span className="thin">{` ${node.first}–${node.last}, ${node.count} sections`}</span>
          </li>
        ))}
      </ol>
      {!nodes.length ? <p className="thin">No heading covers that span.</p> : null}
    </>
  )
}

export function OutlineView({ here, go }) {
  const url = here.code && here.start && here.end
    ? route('/outline', { code: here.code, start: here.start, end: here.end, session: here.session })
    : ''
  const { body, loading } = useJson(url)
  if (!url) return <p className="thin">Name a book and two section numbers.</p>
  if (loading && !body) return <p className="thin">Reading the headings.</p>
  if (!body) return null
  if (!body.found) return <p className="miss">{reasonWords(body)}</p>
  return <Outline body={body} go={go} asked={here} />
}

/* One expression: a section, a span, a named act, or a session credit. */
export function Cite({ here, go }) {
  const url = here.q ? route('/cite', { q: here.q, session: here.session }) : ''
  const { body, loading } = useJson(url)
  if (!url) return <p className="thin">Write a citation.</p>
  if (loading && !body) return <p className="thin">Opening the citation.</p>
  if (!body) return null
  if (!body.found) {
    return (
      <>
        <h1>{here.q}</h1>
        <p className="miss">{reasonWords(body)}</p>
        {body.statute ? (
          <p className="thin">
            {`The official place is United States Code title ${body.statute.title}`}
            {body.statute.chapter ? `, chapter ${body.statute.chapter}` : ''}
            {body.regulations ? `, and ${body.regulations.title} CFR` : ''}
            .
          </p>
        ) : null}
        <p className="beside">
          <Link href={searchHref({ q: here.q })} go={go}>search for those words instead</Link>
        </p>
      </>
    )
  }
  if (body.kind === 'session') {
    return (
      <>
        <h1>{body.reference}</h1>
        <p className="thin">{`Statutes of ${body.year}, chapter ${body.chapter}`}</p>
        <p className="beside">
          <span className="thin">target</span>
          <span>{body.target}</span>
        </p>
        <p className="thin">A session chapter is not a code section. It is not opened here.</p>
      </>
    )
  }
  if (body.nodes) return <Outline body={body} go={go} asked={here} />
  if (body.code && body.section) {
    return (
      <>
        <h1>{body.citation}</h1>
        <p className="beside">
          <Link href={sectionHref(body.code, body.section)} go={go}>open the section</Link>
          {body.subdivision ? <span className="thin">{`subdivision ${body.subdivision}`}</span> : null}
        </p>
      </>
    )
  }
  return <p className="miss">{reasonWords(body)}</p>
}

/* The annotations recorded when a section was indexed. A note is a `Note`
 * member; a target is the word that note kept. */
export function Annotations({ here, notes, codes, go }) {
  const [asked, setAsked] = useState(here)
  useEffect(() => { setAsked(here) }, [here])
  const url = route('/annotations', {
    note: here.note, code: here.code, target: here.target, limit: here.limit || 40,
  })
  const { body, loading } = useJson(url)
  const rows = (body && body.annotations) || []
  function change(name, value) {
    setAsked((was) => ({ ...was, [name]: value }))
  }
  return (
    <>
      <h1>Stored annotations</h1>
      <form
        className="find wide"
        onSubmit={(event) => {
          event.preventDefault()
          go(event, annotationsHref({
            note: asked.note, code: asked.code, target: asked.target, limit: asked.limit,
          }))
        }}
      >
        <label>
          Note
          <select value={asked.note || ''} onChange={(event) => change('note', event.target.value)}>
            <option value="">every note</option>
            {notes.map((kind) => <option key={kind} value={kind}>{noteWords(kind)}</option>)}
          </select>
        </label>
        <label>
          Book
          <select value={asked.code || ''} onChange={(event) => change('code', event.target.value)}>
            <option value="">every book</option>
            {codes.map((row) => <option key={row.code} value={row.code}>{row.code}</option>)}
          </select>
        </label>
        <label>
          Target
          <input
            value={asked.target || ''}
            onChange={(event) => change('target', event.target.value)}
          />
        </label>
        <button>Show</button>
      </form>
      {loading && !body ? <p className="thin">Reading the table.</p> : null}
      {!rows.length && body && !loading ? (
        <p className="thin">
          No row is stored for that. A note added after the last pass has no rows yet.
        </p>
      ) : null}
      {rows.length ? (
        <ol className="hits">
          {rows.map((row, index) => (
            <li key={index}>
              <p className="hit-head">
                <Link
                  href={`/view/section/${row.code}/${String(row.citation || '').split(' ').pop()}`}
                  go={go}
                >
                  {row.citation}
                </Link>
                <mark className={`note-${row.note}`}>{noteWords(row.note)}</mark>
                {row.target ? <span className="thin">{row.target}</span> : null}
                {row.cite ? <span className="thin">{row.cite}</span> : null}
                {row.join ? <span className="thin">{row.join}</span> : null}
              </p>
              {row.text ? <p className="hit-words">{row.text}</p> : null}
            </li>
          ))}
        </ol>
      ) : null}
    </>
  )
}
