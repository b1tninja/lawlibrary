import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'

const LEGEND = [
  ['note-amount', 'amount'],
  ['note-period', 'period'],
  ['note-date', 'date'],
  ['note-citation', 'citation'],
  ['note-cross_reference', 'cross reference'],
  ['note-case', 'name'],
  ['note-cut', 'cut'],
  ['note-short_form', 'short form'],
  ['note-named_act', 'named act'],
  ['note-session', 'session'],
]

function usePlace() {
  const [place, setPlace] = useState(window.location.pathname + window.location.search)
  useEffect(() => {
    const onPop = () => setPlace(window.location.pathname + window.location.search)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  function go(event, href) {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) {
      return
    }
    event.preventDefault()
    window.history.pushState({}, '', href)
    setPlace(href)
  }
  return [place, go]
}

function readPlace(place) {
  const url = new URL(place, 'http://local')
  const parts = url.pathname.split('/').filter(Boolean)
  if (parts[0] === 'view' && parts[1] === 'section' && parts.length >= 4) {
    return { kind: 'section', code: parts[2], number: decodeURIComponent(parts[3]) }
  }
  if (parts[0] === 'view' && parts[1] === 'open') {
    return { kind: 'section', code: url.searchParams.get('code') || '', number: url.searchParams.get('section') || '' }
  }
  if (parts[0] === 'view' && parts[1] === 'search') {
    return { kind: 'search', q: url.searchParams.get('q') || '' }
  }
  if (parts[0] === 'view' && parts[1] === 'tree') {
    return { kind: 'tree', url: parts.slice(2).map(decodeURIComponent).join('/') }
  }
  if (parts.length === 0 || (parts[0] === 'view' && parts.length === 1)) {
    return { kind: 'tree', url: '' }
  }
  return { kind: 'leave' }
}

function Link({ href, go, children }) {
  return <a href={href} onClick={(event) => go(event, href)}>{children}</a>
}

function Find({ codes, go }) {
  const [code, setCode] = useState(codes[0] || '')
  const [number, setNumber] = useState('')
  return (
    <form className="find" onSubmit={(event) => {
      event.preventDefault()
      if (code && number) {
        go(event, `/view/section/${encodeURIComponent(code)}/${encodeURIComponent(number)}`)
      }
    }}>
      <label>Code <select name="code" value={code} onChange={(event) => setCode(event.target.value)}>
        {codes.map((token) => <option key={token} value={token}>{token}</option>)}
      </select></label>
      <label>Section <input name="section" value={number} onChange={(event) => setNumber(event.target.value)} /></label>
      <button>Open</button>
    </form>
  )
}

function Tree({ url, go }) {
  const [node, setNode] = useState(null)
  useEffect(() => {
    let live = true
    fetch('/tree/' + url.split('/').map(encodeURIComponent).join('/'))
      .then((response) => response.json())
      .then((body) => { if (live) setNode(body) })
    return () => { live = false }
  }, [url])
  if (!node) return <p>Loading the library.</p>
  if (!node.found) return <p>That node is not in the index.</p>
  const codes = (node.children || []).filter((child) => child.unit === 'code').map((child) => child.value)
  return (
    <>
      {codes.length ? <Find codes={codes} go={go} /> : null}
      <h1>{node.url || 'us-ca'}</h1>
      {node.children && node.children.length ? (
        <ul>
          {node.children.map((child) => {
            const href = child.unit === 'section' && node.code
              ? `/view/section/${node.code}/${child.value}`
              : `/view/tree/${child.url}`
            const label = child.heading || child.value || child.url
            return <li key={child.url}><Link href={href} go={go}>{label}</Link></li>
          })}
        </ul>
      ) : <p>No further headings.</p>}
    </>
  )
}

const HOVER_MS = 700

function termHref(term, code, note, target) {
  const params = new URLSearchParams()
  if (term) params.set('q', term)
  if (code) params.set('code', code)
  if (note) params.set('note', note)
  if (target) params.set('target', target)
  return '/term?' + params.toString()
}

function Term({ term, code, note, target, go, children }) {
  const [card, setCard] = useState(null)
  const [pinned, setPinned] = useState(false)
  const wait = useState({ id: 0 })[0]
  function dismiss() {
    window.clearTimeout(wait.id)
    if (!pinned) setCard(null)
  }
  function hover() {
    window.clearTimeout(wait.id)
    wait.id = window.setTimeout(() => {
      fetch(termHref(term, code, note, target))
        .then((response) => response.json())
        .then((body) => setCard(body))
    }, HOVER_MS)
  }
  return (
    <span className="term" onMouseEnter={hover} onMouseLeave={dismiss}>
      {children}
      {card && card.found ? (
        <span className={pinned ? 'term-card pinned' : 'term-card'} onClick={() => setPinned(true)}>
          <strong>{card.term}</strong>
          <span className="term-kind">{card.kind}</span>
          <span className="term-count">
            {card.frequency.pf} here, {card.frequency.df} sections
            {card.frequency.indexed != null ? `, ${card.frequency.indexed} indexed` : ''}
          </span>
          {card.neighbors && card.neighbors.length ? (
            <span className="term-neighbors">
              {card.neighbors.map((item) => (
                <button key={item.phrase} type="button" onClick={(event) => {
                  event.stopPropagation()
                  fetch(termHref(item.phrase, code)).then((response) => response.json()).then(setCard)
                }}>{item.phrase}</button>
              ))}
            </span>
          ) : null}
          {card.occurrences && card.occurrences.length ? (
            <ul>
              {card.occurrences.map((hit) => (
                <li key={hit.href || hit.citation}>
                  {hit.href ? <Link href={hit.href} go={go}>{hit.citation || hit.href}</Link> : hit.citation}
                </li>
              ))}
            </ul>
          ) : null}
        </span>
      ) : null}
    </span>
  )
}

function Words({ text, code, go }) {
  const parts = String(text || '').split(/(\s+)/)
  return parts.map((part, index) => {
    const term = part.replace(/^[^A-Za-z0-9$]+|[^A-Za-z0-9$]+$/g, '')
    if (!term) return <span key={index}>{part}</span>
    return <Term key={index} term={term} code={code} go={go}>{part}</Term>
  })
}

function Marks({ pieces, text, code, go }) {
  if (!pieces || !pieces.length) return <Words text={text} code={code} go={go} />
  return pieces.map((piece, index) => {
    if (!piece.kind) return <Words key={index} text={piece.text} code={code} go={go} />
    const mark = (
      <Term term={piece.text} code={code} note={piece.kind} target={piece.title} go={go}>
        <mark className={`note-${piece.kind}`} data-note={piece.kind} title={piece.title}>{piece.text}</mark>
      </Term>
    )
    return piece.href ? <Link key={index} href={piece.href} go={go}>{mark}</Link> : <span key={index}>{mark}</span>
  })
}

function SearchBox({ go, initial }) {
  const [q, setQ] = useState(initial || '')
  return (
    <form className="find" onSubmit={(event) => {
      event.preventDefault()
      if (q.trim()) go(event, '/view/search?q=' + encodeURIComponent(q.trim()))
    }}>
      <label>Search <input name="q" value={q} onChange={(event) => setQ(event.target.value)} /></label>
      <button>Find</button>
    </form>
  )
}

function SearchResults({ q, go }) {
  const [body, setBody] = useState(null)
  useEffect(() => {
    let live = true
    fetch('/search?q=' + encodeURIComponent(q))
      .then((response) => response.json())
      .then((payload) => { if (live) setBody(payload) })
    return () => { live = false }
  }, [q])
  if (!body) return <p>Searching.</p>
  if (!body.found) return <p>No matches.</p>
  return (
    <>
      <h1>{body.q}</h1>
      <ul className="contents">
        {(body.hits || []).map((hit) => (
          <li key={hit.href || hit.citation}>
            {hit.href ? <Link href={hit.href} go={go}>{hit.citation}</Link> : hit.citation}
            {hit.snippet ? <p>{hit.snippet}</p> : null}
          </li>
        ))}
      </ul>
    </>
  )
}

function Section({ code, number, go }) {
  const [body, setBody] = useState(null)
  useEffect(() => {
    let live = true
    fetch(`/section/${encodeURIComponent(code)}/${encodeURIComponent(number)}`)
      .then((response) => response.json())
      .then((payload) => { if (live) setBody(payload) })
    return () => { live = false }
  }, [code, number])
  if (!body) return <p>Loading the section.</p>
  if (!body.found) return <p>That section is not in the index.</p>
  return (
    <>
      {(body.path || []).map((step) => <p className="path" key={step.heading}>{step.heading}</p>)}
      <h1>{body.citation || `${code} ${number}`}</h1>
      <p className="beside">
        {body.previous ? <Link href={`/view/section/${code}/${body.previous}`} go={go}>Previous</Link> : null}
        {' '}
        {body.next ? <Link href={`/view/section/${code}/${body.next}`} go={go}>Next</Link> : null}
      </p>
      <ul className="legend">
        {LEGEND.map(([kind, label]) => <li key={kind}><mark className={kind}>{label}</mark></li>)}
      </ul>
      <article><Marks pieces={body.pieces} text={body.text} code={code} go={go} /></article>
      {body.history ? <p className="history">{body.history}</p> : null}
      {body.links && body.links.length ? (
        <ul className="contents">
          {body.links.map((link) => <li key={link.href}><Link href={link.href} go={go}>{link.label}</Link></li>)}
        </ul>
      ) : null}
    </>
  )
}

function Shell({ place, go }) {
  const here = readPlace(place)
  return (
    <>
      <nav>
        <Link href="/" go={go}>Library</Link>
        <a href="/mirror">Reference</a>
        <a href="/view/diagram/codes">Codes</a>
        <a href="/view/diagram/vesting?code=GOV">Vesting</a>
        <a href="/view/diagram/enactments?code=WAT">Enactments</a>
        <SearchBox go={go} initial={here.kind === 'search' ? here.q : ''} />
      </nav>
      <main id="main">
        {here.kind === 'section' ? <Section code={here.code} number={here.number} go={go} /> : null}
        {here.kind === 'tree' ? <Tree url={here.url} go={go} /> : null}
        {here.kind === 'search' ? <SearchResults q={here.q} go={go} /> : null}
      </main>
    </>
  )
}

const root = document.getElementById('root')
const place = window.location.pathname
if (root && !place.startsWith('/view/diagram') && !place.startsWith('/mirror')) {
  function App() {
    const [here, go] = usePlace()
    return <Shell place={here} go={go} />
  }
  createRoot(root).render(<App />)
}
