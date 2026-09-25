/* Where the client is. One place object per view, and the href that opens it.
 *
 * The server answers with its own links, which are the script-free pages under
 * `/view`. `local` turns one of those into the same place inside the reader, so
 * a payload never has to know a route.
 */

export const HOME = '/reader'

const VIEWS = new Set([
  'tree', 'section', 'search', 'cite', 'outline', 'diagram', 'closure',
  'annotations', 'graph',
])

export const CLOSURE_UNITS = [
  'division', 'title', 'part', 'chapter', 'article', 'section', 'subdivision',
]

function clean(params) {
  const search = new URLSearchParams()
  Object.keys(params || {}).forEach((name) => {
    const value = params[name]
    if (value === undefined || value === null || value === '' || value === false) return
    search.set(name, value === true ? '1' : String(value))
  })
  const text = search.toString()
  return text ? '?' + text : ''
}

function segments(url) {
  return String(url || '').split('/').filter(Boolean).map(encodeURIComponent).join('/')
}

export function libraryHref(url) {
  const path = segments(url)
  return path ? `${HOME}/tree/${path}` : HOME
}

export function sectionHref(code, number, params) {
  return `${HOME}/section/${encodeURIComponent(code)}/${encodeURIComponent(number)}${clean(params)}`
}

export function searchHref(params) {
  return `${HOME}/search${clean(params)}`
}

export function citeHref(q, session) {
  return `${HOME}/cite${clean({ q, session })}`
}

export function outlineHref(params) {
  return `${HOME}/outline${clean(params)}`
}

export function diagramHref(kind, code) {
  return `${HOME}/diagram/${encodeURIComponent(kind)}${clean({ code })}`
}

export function annotationsHref(params) {
  return `${HOME}/annotations${clean(params)}`
}

export function graphHref(params) {
  return `${HOME}/graph${clean(params)}`
}

export function closureHref(params) {
  return `${HOME}/closure${clean(params)}`
}

/* A link the server sent, as a place in this client. `/view/x` is `/reader/x`.
 * Anything else, such as `/mirror` or a representation of a section, is left
 * alone so the browser opens it. */
export function local(href) {
  const text = String(href || '')
  if (!text) return ''
  if (text === '/' || text === '/view') return HOME
  if (text.startsWith('/view/')) return HOME + text.slice('/view'.length)
  return text
}

export function isLocal(href) {
  const text = String(href || '')
  return text === '/' || text === '/view' || text.startsWith('/view/') || text.startsWith(HOME)
}

export function readPlace(place) {
  const url = new URL(place || HOME, 'http://local')
  const asked = url.searchParams
  const one = (name) => asked.get(name) || ''
  let parts = url.pathname.split('/').filter(Boolean)
  if (parts[0] === 'reader' || parts[0] === 'view') parts = parts.slice(1)
  const kind = parts[0] || ''
  if (!kind) return { kind: 'library', url: '' }
  if (!VIEWS.has(kind)) return { kind: 'leave' }
  if (kind === 'tree') {
    return { kind: 'library', url: parts.slice(1).map(decodeURIComponent).join('/') }
  }
  if (kind === 'section' && parts.length >= 3) {
    return {
      kind: 'section',
      code: decodeURIComponent(parts[1]).toUpperCase(),
      number: decodeURIComponent(parts[2]),
      session: one('session'),
      cut: one('cut'),
    }
  }
  if (kind === 'search') {
    return {
      kind: 'search',
      q: one('q'),
      code: one('code'),
      start: one('start'),
      end: one('end'),
      session: one('session'),
      limit: one('limit'),
    }
  }
  if (kind === 'cite') return { kind: 'cite', q: one('q'), session: one('session') }
  if (kind === 'outline') {
    return {
      kind: 'outline',
      code: one('code'),
      start: one('start'),
      end: one('end'),
      session: one('session'),
    }
  }
  if (kind === 'diagram' && parts[1]) {
    return { kind: 'diagram', diagram: decodeURIComponent(parts[1]), code: one('code') }
  }
  if (kind === 'annotations') {
    return {
      kind: 'annotations',
      note: one('note'),
      code: one('code'),
      target: one('target'),
      limit: one('limit'),
    }
  }
  if (kind === 'graph') {
    return {
      kind: 'graph',
      code: one('code'),
      section: one('section'),
      hops: one('hops') || '1',
      only: one('only'),
      same: one('same'),
      session: one('session'),
    }
  }
  if (kind === 'closure') {
    const sent = { kind: 'closure', use: one('use'), code: one('code') }
    CLOSURE_UNITS.forEach((unit) => { sent[unit] = one(unit) })
    sent.session = one('session')
    sent.hops = one('hops')
    sent.only = one('only')
    sent.same = one('same')
    sent.q = one('q')
    return sent
  }
  return { kind: 'leave' }
}

/* The words a miss says, keyed by the reason the server recorded. */
const REASONS = {
  not_in_index: 'That is not in the index.',
  not_indexed: 'That publication year is not indexed.',
  unknown_code: 'That is not one of the books.',
  unknown_book: 'That is not one of the books.',
  unknown_act: 'That named act is not one of the spans.',
  unknown_use: 'A closure reads, finds, walks references, or reports gaps.',
  ordinance_absent: 'A Sacramento ordinance is not in this index.',
  outside_us_ca: 'That is federal law, outside the California index.',
  span_too_large: 'That span is too large for text. The outline is below.',
  hops: 'The walk depth is a number, or all.',
  method: 'Only GET is served.',
  not_found: 'That is not a route in the library.',
}

export function reasonWords(body) {
  if (!body) return 'Nothing came back.'
  const reason = body.reason || ''
  return REASONS[reason] || (reason ? `That is a miss: ${reason}.` : 'That is not in the index.')
}
