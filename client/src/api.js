/* The JSON routes, and the hooks that read them.
 *
 * Every route answers `found`. A miss keeps `reason`, so a view says why
 * instead of showing an empty page. The catalog, the publication years, and
 * the closed sets are read once and kept.
 */

import { useEffect, useMemo, useState } from 'react'

import { clean } from './place.js'

export function route(path, params) {
  return path + clean(params)
}

/* A route asked for once: the open promise while it is in flight, the answer
 * after. Two views that mount together share one GET. */
const asking = new Map()
const held = new Map()

async function read(url, signal) {
  const response = await fetch(url, { signal, headers: { Accept: 'application/json' } })
  const text = await response.text()
  try {
    return JSON.parse(text)
  } catch (error) {
    return { found: false, reason: 'not_found' }
  }
}

/* A request the reader abandoned is not a miss — a view that moved on keeps
 * what it had. Anything else is a miss, so the page says so instead of
 * holding a spinner the server will never answer. */
function gone(error) {
  return Boolean(error) && (error.name === 'AbortError' || error.code === 20)
}

/* One GET. `url` empty holds the view at rest. A second call for the same url
 * while the first is open replaces it, so a fast typist does not race. */
export function useJson(url) {
  const [state, setState] = useState(() => ({ url, body: null, loading: Boolean(url) }))
  useEffect(() => {
    if (!url) {
      setState({ url, body: null, loading: false })
      return undefined
    }
    const controller = new AbortController()
    setState((was) => ({ url, body: was.url === url ? was.body : null, loading: true }))
    read(url, controller.signal).then(
      (body) => setState({ url, body, loading: false }),
      (error) => {
        if (gone(error)) return
        setState({ url, body: { found: false, reason: 'not_found' }, loading: false })
      },
    )
    return () => controller.abort()
  }, [url])
  return state
}

/* A route whose answer does not change while the page is open. */
export function useKept(url, empty) {
  const [body, setBody] = useState(() => held.get(url) || empty)
  useEffect(() => {
    if (held.has(url)) {
      setBody(held.get(url))
      return undefined
    }
    let live = true
    let open = asking.get(url)
    if (!open) {
      open = read(url).then((payload) => {
        held.set(url, payload)
        asking.delete(url)
        return payload
      }, (error) => {
        asking.delete(url)
        throw error
      })
      asking.set(url, open)
    }
    open.then((payload) => { if (live) setBody(payload) }, () => {})
    return () => { live = false }
  }, [url])
  return body
}

const NO_CATALOG = { codes: [], sessions: [] }

export function useCatalog() {
  const books = useKept('/codes', { codes: [] })
  const years = useKept('/sessions', { sessions: [] })
  const codes = books.codes || NO_CATALOG.codes
  const sessions = years.sessions || NO_CATALOG.sessions
  return { codes, sessions }
}

const NO_SURFACE = []

const NO_SURFACES = { surfaces: {}, units: [] }

/* The closed sets, so the legend and the filters are the words the server
 * stores and not a copy kept here — the names of the sets included. Until the
 * route answers there are none, so reach for a set through `members`. */
export function useSurfaces() {
  const body = useKept('/surfaces', NO_SURFACES)
  const sets = body.surfaces || NO_SURFACES.surfaces
  const units = body.units || NO_SURFACES.units
  return useMemo(() => ({ ...sets, units }), [sets, units])
}

/* One closed set by name. A set the server has not answered with yet is
 * empty, and stays the same array, so a view may draw before it arrives. */
export function members(surfaces, name) {
  const held = (surfaces || {})[name]
  return Array.isArray(held) ? held : NO_SURFACE
}

export function codeTitle(codes, token) {
  const row = (codes || []).find((item) => item.code === token)
  return row ? row.title : token
}

/* A route that answers with words rather than JSON: a section as text,
 * Markdown, or XML. */
export function useText(url) {
  const [state, setState] = useState(() => ({ url, raw: '', loading: Boolean(url) }))
  useEffect(() => {
    if (!url) {
      setState({ url, raw: '', loading: false })
      return undefined
    }
    const controller = new AbortController()
    setState({ url, raw: '', loading: true })
    fetch(url, { signal: controller.signal })
      .then((reply) => reply.text())
      .then(
        (raw) => setState({ url, raw, loading: false }),
        (error) => { if (!gone(error)) setState({ url, raw: '', loading: false }) },
      )
    return () => controller.abort()
  }, [url])
  return state
}
