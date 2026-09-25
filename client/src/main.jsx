/* The reader. React mounts on `#root`; the document inside `noscript` is the
 * same place without a script.
 *
 * Every view is a URL, so a section, a search, a span, a closure, and a graph
 * are all linkable and the back button works.
 */

import { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'

import './reader.css'
import { route, useCatalog, useJson, useSurfaces } from './api.js'
import { Closure, GraphView } from './closure.jsx'
import { Annotations, Cite, OutlineView, Search } from './find.jsx'
import { Graph } from './graph.jsx'
import { Library } from './library.jsx'
import { useShown } from './layers.jsx'
import { Link, TermCard } from './marks.jsx'
import { Reading } from './reading.js'
import { Section } from './section.jsx'
import {
  annotationsHref, citeHref, closureHref, diagramHref, libraryHref,
  readPlace, reasonWords, searchHref, sectionHref,
} from './place.js'

function usePlace() {
  const [place, setPlace] = useState(() => window.location.pathname + window.location.search)
  useEffect(() => {
    const onPop = () => setPlace(window.location.pathname + window.location.search)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  function go(event, href) {
    if (!href) return
    if (event && (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey
      || (event.button !== undefined && event.button !== 0))) {
      return
    }
    if (event && event.preventDefault) event.preventDefault()
    if (href === window.location.pathname + window.location.search) return
    window.history.pushState({}, '', href)
    setPlace(href)
    window.scrollTo(0, 0)
  }
  return [place, go]
}

/* A stored graph: the books that cite each other, where an office was vested,
 * and which chapter enacted a section. */
function DiagramView({ diagram, code, codes, go }) {
  const { body, loading } = useJson(route(`/diagram/${encodeURIComponent(diagram)}`, { code }))
  const needs = diagram !== 'codes'
  return (
    <>
      <h1>{diagram}</h1>
      <p className="beside">
        {['codes', 'vesting', 'enactments'].map((kind) => (
          <Link key={kind} href={diagramHref(kind, kind === 'codes' ? '' : (code || ''))} go={go}>
            {kind === diagram ? `✓ ${kind}` : kind}
          </Link>
        ))}
        {needs ? (
          <label>
            Book
            <select
              value={code || ''}
              onChange={(event) => go(null, diagramHref(diagram, event.target.value))}
            >
              <option value="">every book</option>
              {codes.map((row) => <option key={row.code} value={row.code}>{row.code}</option>)}
            </select>
          </label>
        ) : null}
      </p>
      {loading && !body ? <p className="thin">Reading the stored edges.</p> : null}
      {body && !body.found ? <p className="miss">{reasonWords(body)}</p> : null}
      {body && body.found ? (
        <Graph
          edges={body.edges}
          go={go}
          empty="No edge of that kind is stored. The needle pass records them when a section is indexed."
        />
      ) : null}
    </>
  )
}

function Ask({ here, go }) {
  const [words, setWords] = useState(here.q || '')
  const box = useRef(null)
  useEffect(() => { setWords(here.q || '') }, [here.q])
  useEffect(() => {
    function onKey(event) {
      if (event.key === '/' && event.target === document.body) {
        event.preventDefault()
        if (box.current) box.current.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  return (
    <form
      className="ask"
      onSubmit={(event) => {
        event.preventDefault()
        const asked = words.trim()
        if (!asked) return
        go(event, /^[A-Za-z][A-Za-z. ]*\s+\d/.test(asked) ? citeHref(asked) : searchHref({ q: asked }))
      }}
    >
      <input
        ref={box}
        value={words}
        placeholder={'a citation, or words to find   /'}
        aria-label="A citation or words"
        onChange={(event) => setWords(event.target.value)}
      />
      <button title="A citation opens; words search">Open</button>
      <button
        type="button"
        className="plain"
        onClick={(event) => { if (words.trim()) go(event, searchHref({ q: words.trim() })) }}
      >
        find
      </button>
    </form>
  )
}

const KEYS = [
  ['/', 'the citation and search bar'],
  ['j / k', 'the next and previous section'],
  ['g then l', 'the library'],
  ['g then f', 'search'],
  ['g then c', 'a closure'],
  ['g then d', 'the stored graphs'],
  ['g then a', 'the stored annotations'],
  ['double-click', 'look up the word under the pointer'],
  ['?', 'this list'],
]

function Keys({ onClose }) {
  return (
    <aside className="keys">
      <p className="term-title">
        <strong>Keys</strong>
        <span className="term-shut">
          <button type="button" onClick={onClose}>{'×'}</button>
        </span>
      </p>
      <dl>
        {KEYS.map(([key, words]) => (
          <div key={key}>
            <dt><kbd>{key}</kbd></dt>
            <dd>{words}</dd>
          </div>
        ))}
      </dl>
    </aside>
  )
}

/* One handler for the whole reader, so a key means the same thing everywhere. */
function useKeys({ go, sides, setHelp, close }) {
  const waiting = useRef('')
  useEffect(() => {
    function onKey(event) {
      const tag = (event.target && event.target.tagName) || ''
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') {
        if (event.key === 'Escape') event.target.blur()
        return
      }
      if (event.metaKey || event.ctrlKey || event.altKey) return
      if (event.key === 'Escape') { waiting.current = ''; close(); return }
      if (waiting.current === 'g') {
        waiting.current = ''
        const where = {
          l: libraryHref(''),
          f: searchHref({}),
          c: closureHref({}),
          d: diagramHref('codes', ''),
          a: annotationsHref({}),
        }[event.key]
        if (where) { event.preventDefault(); go(null, where) }
        return
      }
      if (event.key === 'g') { waiting.current = 'g'; return }
      if (event.key === '?') { event.preventDefault(); setHelp((was) => !was); return }
      if (event.key === 'j' && sides.current.next) {
        event.preventDefault()
        go(null, sectionHref(sides.current.code, sides.current.next, sides.current.params))
      }
      if (event.key === 'k' && sides.current.previous) {
        event.preventDefault()
        go(null, sectionHref(sides.current.code, sides.current.previous, sides.current.params))
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go, setHelp, close, sides])
}

function title(here) {
  if (here.kind === 'section') return `${here.code} ${here.number}`
  if (here.kind === 'library') return here.url ? here.url.toUpperCase() : 'Law library'
  if (here.kind === 'search') return here.q ? `${here.q} — search` : 'Search'
  if (here.kind === 'cite') return here.q || 'A citation'
  if (here.kind === 'outline') return `${here.code} ${here.start}–${here.end}`
  if (here.kind === 'diagram') return here.diagram
  if (here.kind === 'graph') return `${here.code} ${here.section} — references`
  if (here.kind === 'closure') return 'A closure'
  if (here.kind === 'annotations') return 'Annotations'
  return 'Law library'
}

function Shell() {
  const [place, go] = usePlace()
  const here = readPlace(place)
  const { codes, sessions } = useCatalog()
  const surfaces = useSurfaces()
  const [shown, act] = useShown()
  const [looking, setLooking] = useState(null)
  const [kept, setKept] = useState([])
  const [help, setHelp] = useState(false)
  const sides = useRef({ code: '', previous: '', next: '', params: {} })
  useKeys({
    go,
    sides,
    setHelp,
    close: () => { setLooking(null); setHelp(false) },
  })
  useEffect(() => {
    document.title = `${title(here)} — Law Library`
  }, [place])
  useEffect(() => {
    sides.current = { code: '', previous: '', next: '', params: {} }
  }, [place])
  useEffect(() => {
    if (!looking) return undefined
    function away(event) {
      if (event.target.closest && event.target.closest('.term-card, mark, .legend-toggle')) return
      setLooking(null)
    }
    document.addEventListener('mousedown', away)
    return () => document.removeEventListener('mousedown', away)
  }, [looking])
  const reading = {
    shown,
    act,
    look: (detail) => setLooking(detail),
    go,
  }
  return (
    <Reading.Provider value={reading}>
      <header className="mast">
        <p>Law Library</p>
        <nav className="site">
          <Link href={libraryHref('')} go={go}>Library</Link>
          <Link href={searchHref({})} go={go}>Search</Link>
          <Link href={closureHref({})} go={go}>Closure</Link>
          <Link href={diagramHref('codes', '')} go={go}>Graphs</Link>
          <Link href={annotationsHref({})} go={go}>Annotations</Link>
          <a href="/view/random">Random</a>
          <a href="/mirror">Reference</a>
          <button type="button" className="plain" onClick={() => setHelp(true)}>keys</button>
        </nav>
        <Ask here={here} go={go} />
      </header>
      <main id="main">
        {here.kind === 'library' ? <Library url={here.url} go={go} /> : null}
        {here.kind === 'section' ? (
          <Section
            key={`${here.code}/${here.number}/${here.session}`}
            code={here.code}
            number={here.number}
            session={here.session}
            sessions={sessions}
            order={surfaces.layer}
            sides={sides}
            go={go}
          />
        ) : null}
        {here.kind === 'search' ? (
          <Search here={here} codes={codes} sessions={sessions} go={go} />
        ) : null}
        {here.kind === 'cite' ? <Cite here={here} go={go} /> : null}
        {here.kind === 'outline' ? <OutlineView here={here} go={go} /> : null}
        {here.kind === 'diagram' ? (
          <DiagramView diagram={here.diagram} code={here.code} codes={codes} go={go} />
        ) : null}
        {here.kind === 'graph' ? <GraphView here={here} go={go} /> : null}
        {here.kind === 'closure' ? (
          <Closure here={here} codes={codes} sessions={sessions} go={go} />
        ) : null}
        {here.kind === 'annotations' ? (
          <Annotations here={here} notes={surfaces.note} codes={codes} go={go} />
        ) : null}
        {here.kind === 'leave' ? (
          <p className="miss">
            That is not a view in the reader. The library is <Link href={libraryHref('')} go={go}>here</Link>.
          </p>
        ) : null}
      </main>
      {kept.length ? (
        <aside className="keeps">
          {kept.map((card, index) => (
            <TermCard
              key={`${card.term}${index}`}
              looking={card}
              go={go}
              pinned
              onClose={() => setKept((was) => was.filter((_item, place2) => place2 !== index))}
            />
          ))}
        </aside>
      ) : null}
      {looking ? (
        <TermCard
          looking={looking}
          go={go}
          onClose={() => setLooking(null)}
          onPin={(card) => {
            setKept((was) => (was.some((item) => item.term === card.term) ? was : was.concat(card)))
            setLooking(null)
          }}
        />
      ) : null}
      {help ? <Keys onClose={() => setHelp(false)} /> : null}
    </Reading.Provider>
  )
}

const root = document.getElementById('root')
if (root) createRoot(root).render(<Shell />)
