"""Advertise version and feature flags so an agent can tell a stale server."""

from __future__ import annotations

# Bump when a tool or a gate changes in a way an agent must notice.
FEATURES = (
    'search',
    'section',
    'citation',
    'shelf',
    'history',
    'succession',
    'title24',
    'style',
    'pins',
    'reader',
    'confirm_gate',
    'write_overwrite_guard',
)

# The first word is the effect where there is one. ``send_`` fetches, rebuilds,
# or starts the local reader, and returns a plan until ``confirm=true``.
# ``write_`` writes a pin and refuses to replace one unless ``overwrite=true``.
# Every other name only reads. ``pin_section``, ``serve_reader``, and
# ``_named_codes`` are the names already registered; they call the same code.
TOOLS = (
    'server_status',
    'list_governments',
    'list_corpora',
    'list_codes',
    'tree_law',
    'list_sessions',
    'search_law',
    '_named_codes',
    'get_section',
    'place',
    'cite_law',
    'outline_law',
    'act_law',
    'range_law',
    'section_history',
    'law_changes',
    'successor_sections',
    'predecessor_sections',
    'recodification_coverage',
    'federal_section',
    'building_standard',
    'standard_adoption',
    'search_span',
    'list_offices',
    'list_courts',
    'analyze_text',
    'list_pins',
    'write_pin_section',
    'pin_section',
    'list_sources',
    'sample_book',
    'list_style_manuals',
    'search_style_manual',
    'common_terms',
    'annotations_law',
    'related_law',
    'diagram_law',
    'review_law',
    'send_reader',
    'serve_reader',
)

INSTRUCTIONS = """\
lawlibrary reads a local index of official statute text. Sacramento, California \
is home. Use it to search that index, open a section, and list the codes. Do not \
scrape a commercial host. A miss stays a miss.

Names tell the effect. send_ fetches from the network, rebuilds an index, or \
starts or stops the local reader. Without confirm=true it returns a plan and \
does nothing. write_ stores a pin. It refuses to replace pins already stored \
for that citation unless overwrite=true. Every other tool only reads.

Download and a full reindex stay on the command line (python ca.py). They are \
not tools. If a later tool does either job, its name starts with send_ and it \
is confirm-gated.

Start with server_status when a tool seems missing (restart the server if the \
list is stale). Then list_codes, search_law, and get_section.
"""


def _version() -> str:
    try:
        from importlib.metadata import version
        return version('lawlibrary')
    except Exception:
        return '0.2.0'


def capabilities() -> dict:
    """Version, feature flags, and the tool names this server registers."""
    return {
        'name': 'lawlibrary',
        'version': _version(),
        'features': list(FEATURES),
        'tools': list(TOOLS),
        'tool_count': len(TOOLS),
        'next': (
            'Read with list_codes, search_law, and get_section. '
            'send_reader and any later send_ tool return a plan until confirm=true. '
            'write_pin_section refuses to replace stored pins unless overwrite=true. '
            'If this list is missing a name you were told exists, restart the server.'
        ),
    }
