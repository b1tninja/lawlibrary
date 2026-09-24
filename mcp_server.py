"""MCP server over the local California code index.

The index is built only from publications at
https://downloads.leginfo.legislature.ca.gov/
"""

from mcp.server.fastmcp import FastMCP

from indexer import Indexer

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


def main():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
