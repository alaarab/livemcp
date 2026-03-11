"""Local documentation sync and search for Ableton and Max ecosystem docs."""

from .catalog import DOC_SOURCES, DocSource, get_doc_source, list_doc_sources
from .index import DocsIndex, get_docs_root
from .sync import sync_docs

__all__ = [
    "DOC_SOURCES",
    "DocSource",
    "DocsIndex",
    "get_doc_source",
    "get_docs_root",
    "list_doc_sources",
    "sync_docs",
]
