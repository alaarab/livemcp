"""Docs crawler and local index builder."""

from __future__ import annotations

import hashlib
import json
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from .. import __version__
from .catalog import DocSource, list_doc_sources
from .index import DocsIndex

USER_AGENT = f"LiveMCP/{__version__} docs-sync"
BLOCK_TAGS = {
    "article",
    "blockquote",
    "br",
    "dd",
    "div",
    "dt",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "nav",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
    "ol",
}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
SKIP_TAGS = {"script", "style", "noscript", "svg"}


@dataclass
class ParsedDocument:
    """A parsed HTML document with title, links, and extracted text blocks."""

    title: str
    blocks: list[tuple[str | None, str]]
    links: list[str]


class _HtmlDocumentParser(HTMLParser):
    """Extract readable text blocks and same-page links from HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.title_parts: list[str] = []
        self.tokens: list[tuple[str, str]] = []
        self._skip_depth = 0
        self._in_title = False
        self._current_heading_tag: str | None = None
        self._text_parts: list[str] = []
        self._heading_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        if tag == "title":
            self._in_title = True

        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

        if tag in BLOCK_TAGS:
            self._flush_text()

        if tag in HEADING_TAGS:
            self._current_heading_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return

        if tag == "title":
            self._in_title = False

        if tag == self._current_heading_tag:
            heading = _clean_text(" ".join(self._heading_parts))
            if heading:
                self.tokens.append(("heading", heading))
            self._heading_parts = []
            self._current_heading_tag = None

        if tag in BLOCK_TAGS:
            self._flush_text()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        if self._current_heading_tag:
            self._heading_parts.append(data)
            return
        self._text_parts.append(data)

    def close(self) -> ParsedDocument:
        super().close()
        self._flush_text()
        current_heading: str | None = None
        blocks: list[tuple[str | None, str]] = []
        for kind, text in self.tokens:
            if kind == "heading":
                current_heading = text
            elif kind == "text":
                blocks.append((current_heading, text))
        return ParsedDocument(
            title=_clean_text(" ".join(self.title_parts)),
            blocks=blocks,
            links=self.links,
        )

    def _flush_text(self) -> None:
        if not self._text_parts:
            return
        text = _clean_text(" ".join(self._text_parts))
        self._text_parts = []
        if text:
            self.tokens.append(("text", text))


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _normalize_url(base_url: str, href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith(("mailto:", "javascript:", "tel:")):
        return None
    absolute = urljoin(base_url, href)
    absolute, _ = urldefrag(absolute)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None
    normalized = parsed._replace(query="").geturl()
    return normalized


def _parse_document(html: str, url: str) -> ParsedDocument:
    parser = _HtmlDocumentParser()
    parser.feed(html)
    parsed = parser.close()
    title = parsed.title or url
    return ParsedDocument(title=title, blocks=parsed.blocks, links=parsed.links)


def _chunk_blocks(blocks: Iterable[tuple[str | None, str]], max_chars: int = 1600) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    buffer: list[str] = []
    active_heading: str | None = None
    size = 0

    for heading, block in blocks:
        if not block:
            continue
        if not buffer:
            active_heading = heading
        elif heading != active_heading and size > max_chars // 2:
            chunks.append(
                {
                    "heading": active_heading or "",
                    "content": "\n\n".join(buffer),
                }
            )
            buffer = []
            size = 0
            active_heading = heading

        if buffer and size + len(block) + 2 > max_chars:
            chunks.append(
                {
                    "heading": active_heading or "",
                    "content": "\n\n".join(buffer),
                }
            )
            buffer = []
            size = 0
            active_heading = heading

        buffer.append(block)
        size += len(block) + 2

    if buffer:
        chunks.append({"heading": active_heading or "", "content": "\n\n".join(buffer)})
    return chunks


def _local_path_for(index: DocsIndex, source_id: str, url: str) -> Path:
    parsed = urlparse(url)
    tail = parsed.path.rstrip("/").split("/")[-1] or "index"
    safe_tail = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in tail).strip("-")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    directory = index.raw_root / source_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{safe_tail or 'page'}-{digest}.html"


def _fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            raise ValueError(f"Unsupported content type for docs sync: {content_type}")
        return response.read().decode("utf-8", errors="replace")


def _crawl_source(
    source: DocSource,
    index: DocsIndex,
    delay_seconds: float,
) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    queue = deque(source.seed_urls)
    visited: set[str] = set()
    pages: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    while queue and len(visited) < source.max_pages:
        current = queue.popleft()
        if current in visited or not source.matches(current):
            continue

        try:
            html = _fetch_html(current)
            parsed = _parse_document(html, current)
            local_path = _local_path_for(index, source.source_id, current)
            local_path.write_text(html, encoding="utf-8")
        except Exception as exc:
            visited.add(current)
            errors.append({"url": current, "error": str(exc)})
            continue

        chunks = _chunk_blocks(parsed.blocks)
        text_content = "\n\n".join(chunk["content"] for chunk in chunks)
        if not text_content:
            visited.add(current)
            continue

        pages.append(
            {
                "url": current,
                "title": parsed.title,
                "local_path": str(local_path),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": hashlib.sha256(text_content.encode("utf-8")).hexdigest(),
                "text_content": text_content,
                "chunks": chunks,
            }
        )
        visited.add(current)

        for href in parsed.links:
            normalized = _normalize_url(current, href)
            if normalized and normalized not in visited and source.matches(normalized):
                queue.append(normalized)

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    return pages, errors


def sync_docs(
    source_ids: list[str] | None = None,
    root: Path | None = None,
    delay_seconds: float = 0.05,
) -> dict[str, object]:
    """Sync configured docs sources into the local raw snapshot and search index."""
    index = DocsIndex(root=root)
    selected_source_ids = set(source_ids or [])
    selected_sources = [
        source
        for source in list_doc_sources()
        if not selected_source_ids or source.source_id in selected_source_ids
    ]
    if not selected_sources:
        raise ValueError("No docs sources selected for sync")

    synced_at = datetime.now(timezone.utc).isoformat()
    results: list[dict[str, object]] = []
    for source in selected_sources:
        pages, errors = _crawl_source(source, index=index, delay_seconds=delay_seconds)
        counts = index.replace_source(source.source_id, synced_at=synced_at, pages=pages)
        results.append(
            {
                "source_id": source.source_id,
                "label": source.label,
                "page_count": counts["page_count"],
                "chunk_count": counts["chunk_count"],
                "error_count": len(errors),
                "errors": errors[:20],
            }
        )

    status = index.get_status()
    return {
        "synced_at": synced_at,
        "sources": results,
        "status": status,
        "selected_sources": [source.source_id for source in selected_sources],
    }


def sync_docs_json(source_ids: list[str] | None = None, root: Path | None = None) -> str:
    """Sync docs and return a JSON summary."""
    return json.dumps(sync_docs(source_ids=source_ids, root=root), indent=2)
