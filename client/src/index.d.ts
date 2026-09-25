/* The law library's reading components.
 *
 * A record the server sends is the shape a component takes. The names here are
 * the words the library already uses: a `Piece` is a slice of stored text, a
 * `Span` is one reading over it, a `CutNode` is a subdivision of a section.
 */

import type { Context, ReactNode } from 'react'

/** A click on a link. `event` is null when the caller is not a link. */
export type Go = (event: unknown, href: string) => void

/** A word or a span the reader asked about. */
export interface Looking {
  /** The words under the pointer. */
  term?: string
  /** The same words, as the span recorded them. */
  text?: string
  /** The book the words sit in, such as `CIV`. */
  code?: string
  /** Which parser recorded it: note, canon, clause, mention, relation, needle, abbreviation. */
  layer?: string
  /** The member inside that layer, such as `citation` or `mandatory`. */
  kind?: string
  /** What the reading points at: a citation, a name, or the surface word. */
  target?: string
  /** The sentence the record carries, when it carries one. */
  reading?: string
  /** Where the span opens, as a link. */
  href?: string
  detail?: Record<string, unknown>
  x?: number
  y?: number
}

/** One slice of stored text. A slice with a kind is one annotation. */
export interface Piece {
  text: string
  kind?: string
  title?: string
  cite?: string
  href?: string
}

/** One reading over a run of words, with the two offsets it covers. */
export interface Span {
  layer: string
  kind: string
  start: number
  end: number
  text: string
  target?: string
  reading?: string
  href?: string
  detail?: Record<string, unknown>
}

/** One cut of a section: its label, its words, and the cuts inside it. */
export interface CutNode {
  /** The walk position, such as `0.1.2`. Spans are keyed by it. */
  path: string
  /** The word this book uses at this depth: subdivision, paragraph, clause. */
  unit: string
  label?: string
  pieces?: Piece[]
  children?: CutNode[]
}

/** One rung of the trail above a section. */
export interface Crumb {
  href: string
  label: string
  /** library, country, region, code, division, title, part, chapter, article, section. */
  unit: string
  pieces?: Piece[]
}

/** One child of the open heading. */
export interface Item {
  href: string
  label: string
  unit: string
  /** The bare number, when the child is a section. */
  short?: string
  pieces?: Piece[]
  current?: boolean
}

/** One section a search opened. */
export interface Hit {
  citation: string
  href?: string
  snippet?: string
  path?: { level?: string; heading?: string }[]
}

/** One hop of a citation walk, or one stored edge. */
export interface Edge {
  source: string
  target: string
  label?: string
  weight?: number
  source_href?: string
  target_href?: string
}

/** One section the walk opened. */
export interface WalkNode {
  id: string
  label?: string
  citation?: string
  found?: boolean
  /** How many hops from the section the walk started at. */
  hop?: number
  href?: string
}

/** How many spans of each kind the words carry, by layer then kind. */
export type Counts = Record<string, Record<string, number>>

/** Which readings are drawn. */
export interface Shown {
  layers: string[]
  has(layer: string, kind: string): boolean
  layer(name: string): boolean
  kind(layer: string, kind: string): boolean
}

/** Turning a reading on and off. */
export interface Act {
  toggleLayer(name: string): void
  toggleKind(layer: string, kind: string): void
  onlyKind(layer: string, kind: string): void
}

export interface ReaderProps {
  children?: ReactNode
  /** Added beside the `reader` class the sheet dresses. */
  className?: string
  /** How a link opens. The default keeps the page where it is. */
  go?: Go
  /** What a click on a mark looks up. The default does nothing. */
  look?: (looking: Looking) => void
  /** Which readings are drawn. The default keeps notes and clauses. */
  shown?: Shown
  act?: Act
}

/** The root a page of this library sits in. Wrap the page once. */
export declare function Reader(props: ReaderProps): JSX.Element

export declare const Reading: Context<{
  shown: Shown
  act: Act
  look: (looking: Looking) => void
  go: Go
}>

export interface LinkProps {
  href: string
  go: Go
  title?: string
  className?: string
  children?: ReactNode
}

/** A link into the library. A `/view` path opens the same place in the reader. */
export declare function Link(props: LinkProps): JSX.Element

export interface PiecesProps {
  /** The slices. A slice with a kind is drawn as its note. */
  pieces?: Piece[]
  /** Used when there are no slices. */
  text?: string
  code?: string
}

/** Stored text with each annotation wrapped. */
export declare function Pieces(props: PiecesProps): JSX.Element

export interface LayeredProps {
  /** Every reading over these words. They overlap, and they are drawn nested. */
  spans?: Span[]
  text: string
  code?: string
  path?: string
}

/** One run of words with every reading the reader has left on. */
export declare function Layered(props: LayeredProps): JSX.Element

export interface LayersProps {
  counts?: Counts
  shown: Shown
  act: Act
  /** The layers, in the order they are offered. */
  order?: string[]
}

/** The legend, and the count of every reading on the open section. */
export declare function Layers(props: LayersProps): JSX.Element

export interface CutsProps {
  /** The section as its cuts. */
  tree?: CutNode
  code?: string
  /** Every reading, keyed by the cut `path` it sits in. */
  spans?: Record<string, Span[]> | null
  onCut?: (node: CutNode, mark: string) => void
}

/** A section drawn as the cuts under it, each one foldable. */
export declare function Cuts(props: CutsProps): JSX.Element

export interface CrumbsProps {
  crumbs?: Crumb[]
  go: Go
}

/** The trail from the library down to the open node. */
export declare function Crumbs(props: CrumbsProps): JSX.Element

export interface ContentsProps {
  items?: Item[]
  go: Go
  heading?: string
  /** Offer a box that sifts the list. Shown once the list is long. */
  sift?: boolean
  /** Draw the bare number rather than the caption. */
  short?: boolean
}

/** The ordered children of a heading, with the open one marked. */
export declare function Contents(props: ContentsProps): JSX.Element

export interface HitsProps {
  hits?: Hit[]
  go: Go
}

/** What a search opened: the citation, the heading path, and the words. */
export declare function Hits(props: HitsProps): JSX.Element

export interface GraphProps {
  edges?: Edge[]
  nodes?: WalkNode[]
  go: Go
  /** The node the reader came from. It is drawn as the one in hand. */
  here?: string
  /** What to say when nothing is stored. */
  empty?: string
}

/**
 * A citation graph. A walk of a few sections is drawn as the walk; a whole
 * book-to-book relation is hundreds of edges and is drawn as a grid.
 */
export declare function Graph(props: GraphProps): JSX.Element

export interface TermCardProps {
  looking: Looking | null
  go: Go
  onClose?: () => void
  onPin?: (looking: Looking) => void
  /** Kept in a corner rather than floating where the pointer asked. */
  pinned?: boolean
  /** The count already in hand. Without it the card asks the index. */
  reply?: {
    found?: boolean
    kind?: string
    frequency?: { pf?: number; df?: number; indexed?: number | null }
    neighbors?: { phrase: string; pf?: number }[]
    occurrences?: { citation?: string; href?: string }[]
  }
}

/** What a reading is, and where the rest of it lives. */
export declare function TermCard(props: TermCardProps): JSX.Element

export interface SidesProps {
  code: string
  previous?: string
  next?: string
  session?: string
  go: Go
}

/** The sections on either side, in the tightest heading. */
export declare function Sides(props: SidesProps): JSX.Element

export interface FormatsProps {
  formats?: { hint: string; href: string }[]
}

/** The same section under each representation: html, txt, xml, pdf, md. */
export declare function Formats(props: FormatsProps): JSX.Element

/** One tree of spans over one run of words. A span that runs past the one holding it is cut there. */
export declare function nest(spans: Span[], length: number): {
  start: number
  end: number
  span: Span | null
  children: unknown[]
}

/** Which readings are drawn, and what turns one on. Kept in the browser. */
export declare function useShown(): [Shown, Act]

/** The word a note kind is printed as. */
export declare function noteWords(kind: string): string

export declare const NOTE_WORDS: Record<string, string>
export declare const LAYER_WORDS: Record<string, string>
export declare const LAYER_ORDER: string[]
