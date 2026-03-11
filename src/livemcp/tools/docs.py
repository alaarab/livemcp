"""Local docs search tools for Ableton and Max ecosystem documentation."""

from __future__ import annotations

import json
from typing import TypedDict

from ..docs import DocsIndex


class DocsSearchResult(TypedDict, total=False):
    chunk_id: int
    page_id: int
    source_id: str
    title: str
    url: str
    local_path: str
    heading: str
    snippet: str
    score: float


class DocsStatusInfo(TypedDict, total=False):
    docs_root: str
    db_path: str
    total_pages: int
    total_chunks: int
    configured_sources: list[dict]


def get_docs_status() -> DocsStatusInfo:
    """Get local docs index status and configured sources."""
    return DocsIndex().get_status()


def search_docs(query: str, source_id: str = "all", limit: int = 8) -> str:
    """Search locally synced Ableton and Max documentation.

    Args:
        query: Search terms to match in the local docs index.
        source_id: Limit search to a specific synced source or use 'all'.
        limit: Maximum number of results to return.
    """
    result = DocsIndex().search(query=query, source_id=source_id, limit=limit)
    return json.dumps(result)


def get_docs_chunk(chunk_id: int) -> str:
    """Read a specific synced docs chunk by id."""
    result = DocsIndex().get_chunk(chunk_id)
    return json.dumps(result)


def get_docs_page(page_id: int) -> str:
    """Read a full synced docs page by id."""
    result = DocsIndex().get_page(page_id)
    return json.dumps(result)


TOOLS = [
    get_docs_status,
    search_docs,
    get_docs_chunk,
    get_docs_page,
]
