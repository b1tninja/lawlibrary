"""MCP server over the local California code index.

The index is built only from publications at
https://downloads.leginfo.legislature.ca.gov/
"""

from mcp.server.fastmcp import FastMCP

from indexer import Indexer
import query as law_query

mcp = FastMCP('lawlibrary')


def _indexer():
    return Indexer()


@mcp.tool()
def list_codes() -> list:
    """List California codes present in the local index, with their official titles."""
    return _indexer().list_codes()


@mcp.tool()
def list_sessions() -> list:
    """Session years present in the local index. The newest is the law currently in force."""
    return _indexer().sessions()


@mcp.tool()
def search_law(query: str, limit: int = 10, session: str = '') -> list:
    """Full-text search of codified California law.

    query: words, a phrase, or a citation such as "CIV 1940" or "Civil Code section 1940".
    session: a session year such as "2019", or "all". Empty uses the newest session.
    Returns active sections with the heading path and a short snippet. Use get_section for the full text.
    """
    chosen = session or None
    return _indexer().search_law(query, limit=limit, session=chosen)


@mcp.tool()
def get_section(code: str, section: str, session: str = '') -> list:
    """Return the full text of one active code section.

    code: official abbreviation or title, such as "CIV" or "Civil Code".
    section: section number, such as "1940" or "1940.5".
    session: a session year, or "all". Empty uses the newest session.
    """
    chosen = session or None
    return _indexer().get_section(code, section, session=chosen)


@mcp.tool()
def place(locality: str = 'Sacramento') -> dict:
    """Scope a query to a locality. Sacramento ordinances are absent from this index."""
    return law_query.place(locality=locality)


@mcp.tool()
def cite_law(expression: str, session: str = '') -> dict:
    """Resolve a citation, span, or named act to a section, outline, or miss.

    expression: forms such as "CIV 5806", "Civil Code section 5806",
    "CIV 4000-6150", or "davis-stirling".
    session: a session year, or "all". Empty uses the newest session.
    Payload includes kind: "section" | "outline" | "miss".
    """
    chosen = session or None
    result = law_query.cite(expression, session=chosen)
    if result.get('found') is False:
        result = dict(result)
        result['kind'] = 'miss'
        return result
    result = dict(result)
    if 'nodes' in result:
        result['kind'] = 'outline'
    else:
        result['kind'] = 'section'
    return result


@mcp.tool()
def outline_law(code: str, start: str, end: str, session: str = '') -> dict:
    """Outline heading groups for a numeric section span in one code.

    code: official abbreviation or title, such as "CIV".
    start, end: section numbers, such as "5800" and "5810".
    session: a session year, or "all". Empty uses the newest session.
    """
    chosen = session or None
    return law_query.outline(code, start, end, session=chosen)


@mcp.tool()
def search_span(query: str, code: str = '', start: str = '', end: str = '',
                limit: int = 10, session: str = '') -> list:
    """Full-text search limited to an optional code and numeric section span.

    query: words or a phrase. Does not search Sacramento ordinances.
    code: optional code abbreviation or title.
    start, end: optional section bounds. When both are set, hits outside the span are dropped.
    session: a session year, or "all". Empty uses the newest session.
    """
    chosen = session or None
    return law_query.search(
        query,
        code=code or None,
        start=start or None,
        end=end or None,
        limit=limit,
        session=chosen,
    )


def main():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
