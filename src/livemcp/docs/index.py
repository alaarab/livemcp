"""SQLite-backed local documentation index."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from .catalog import DOC_SOURCES

DEFAULT_DOCS_DIR = Path.home() / ".cache" / "livemcp" / "docs"


def get_docs_root() -> Path:
    """Return the local docs cache root, creating it lazily elsewhere."""
    configured = os.environ.get("LIVEMCP_DOCS_DIR")
    return Path(configured).expanduser() if configured else DEFAULT_DOCS_DIR


def _normalize_query(query: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_.~/#:+-]+", query)
    if not tokens:
        raise ValueError("Search query must contain at least one searchable token")
    escaped_tokens = [token.replace('"', '""') for token in tokens]
    return " AND ".join(f'"{token}"' for token in escaped_tokens)


class DocsIndex:
    """Manages the local SQLite index used by docs tools and resources."""

    def __init__(self, root: Path | None = None):
        self.root = (root or get_docs_root()).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "docs.sqlite3"
        self.raw_root = self.root / "raw"
        self.raw_root.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    text_content TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
                    source_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    heading TEXT,
                    content TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_pages_source_id ON pages(source_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_page_id ON chunks(page_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_source_id ON chunks(source_id);

                CREATE TABLE IF NOT EXISTS sync_state (
                    source_id TEXT PRIMARY KEY,
                    synced_at TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
                    chunk_id UNINDEXED,
                    page_id UNINDEXED,
                    source_id UNINDEXED,
                    url UNINDEXED,
                    title,
                    heading,
                    content,
                    tokenize = 'unicode61'
                );
                """
            )

    def replace_source(
        self,
        source_id: str,
        synced_at: str,
        pages: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Replace the stored pages and chunks for a source in one transaction."""
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            existing_page_ids = [
                row["id"]
                for row in connection.execute(
                    "SELECT id FROM pages WHERE source_id = ? ORDER BY id", (source_id,)
                )
            ]
            if existing_page_ids:
                placeholders = ",".join("?" for _ in existing_page_ids)
                connection.execute("DELETE FROM docs_fts WHERE source_id = ?", (source_id,))
                connection.execute(
                    f"DELETE FROM chunks WHERE page_id IN ({placeholders})",
                    tuple(existing_page_ids),
                )
                connection.execute("DELETE FROM pages WHERE source_id = ?", (source_id,))

            page_count = 0
            chunk_count = 0
            for page in pages:
                cursor = connection.execute(
                    """
                    INSERT INTO pages (
                        source_id, url, title, local_path, fetched_at, content_hash, text_content
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source_id,
                        page["url"],
                        page["title"],
                        page["local_path"],
                        page["fetched_at"],
                        page["content_hash"],
                        page["text_content"],
                    ),
                )
                page_id = cursor.lastrowid
                page_count += 1
                for chunk_index, chunk in enumerate(page["chunks"]):
                    chunk_cursor = connection.execute(
                        """
                        INSERT INTO chunks (page_id, source_id, chunk_index, heading, content)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            page_id,
                            source_id,
                            chunk_index,
                            chunk.get("heading"),
                            chunk["content"],
                        ),
                    )
                    chunk_id = chunk_cursor.lastrowid
                    connection.execute(
                        """
                        INSERT INTO docs_fts (
                            rowid, chunk_id, page_id, source_id, url, title, heading, content
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            chunk_id,
                            chunk_id,
                            page_id,
                            source_id,
                            page["url"],
                            page["title"],
                            chunk.get("heading") or "",
                            chunk["content"],
                        ),
                    )
                    chunk_count += 1

            connection.execute(
                """
                INSERT INTO sync_state (source_id, synced_at, page_count, chunk_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    synced_at = excluded.synced_at,
                    page_count = excluded.page_count,
                    chunk_count = excluded.chunk_count
                """,
                (source_id, synced_at, page_count, chunk_count),
            )
        return {"page_count": page_count, "chunk_count": chunk_count}

    def get_status(self) -> dict[str, Any]:
        """Return the current local docs index status."""
        with self._connect() as connection:
            total_pages = connection.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
            total_chunks = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            rows = connection.execute(
                "SELECT source_id, synced_at, page_count, chunk_count FROM sync_state ORDER BY source_id"
            ).fetchall()

        by_source = {
            row["source_id"]: {
                "synced_at": row["synced_at"],
                "page_count": row["page_count"],
                "chunk_count": row["chunk_count"],
            }
            for row in rows
        }
        return {
            "docs_root": str(self.root),
            "db_path": str(self.db_path),
            "total_pages": total_pages,
            "total_chunks": total_chunks,
            "configured_sources": [
                {
                    "source_id": source.source_id,
                    "label": source.label,
                    "description": source.description,
                    "synced": source.source_id in by_source,
                    "page_count": by_source.get(source.source_id, {}).get("page_count", 0),
                    "chunk_count": by_source.get(source.source_id, {}).get("chunk_count", 0),
                    "synced_at": by_source.get(source.source_id, {}).get("synced_at"),
                }
                for source in DOC_SOURCES.values()
            ],
        }

    def search(self, query: str, source_id: str = "all", limit: int = 8) -> dict[str, Any]:
        """Search locally synced documentation using FTS."""
        if limit < 1:
            raise ValueError("limit must be at least 1")

        match_query = _normalize_query(query)
        sql = """
            SELECT
                c.id AS chunk_id,
                c.page_id AS page_id,
                c.source_id AS source_id,
                p.title AS title,
                p.url AS url,
                p.local_path AS local_path,
                c.heading AS heading,
                snippet(docs_fts, 6, '[', ']', ' … ', 18) AS snippet,
                bm25(docs_fts) AS score
            FROM docs_fts
            JOIN chunks c ON c.id = docs_fts.rowid
            JOIN pages p ON p.id = c.page_id
            WHERE docs_fts MATCH ?
        """
        params: list[Any] = [match_query]
        if source_id != "all":
            sql += " AND c.source_id = ?"
            params.append(source_id)
        sql += " ORDER BY score LIMIT ?"
        params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(sql, params).fetchall()

        return {
            "query": query,
            "source_id": source_id,
            "limit": limit,
            "results": [
                {
                    "chunk_id": row["chunk_id"],
                    "page_id": row["page_id"],
                    "source_id": row["source_id"],
                    "title": row["title"],
                    "url": row["url"],
                    "local_path": row["local_path"],
                    "heading": row["heading"],
                    "snippet": row["snippet"],
                    "score": row["score"],
                }
                for row in rows
            ],
        }

    def get_chunk(self, chunk_id: int) -> dict[str, Any]:
        """Return a full documentation chunk by id."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    c.id AS chunk_id,
                    c.page_id AS page_id,
                    c.source_id AS source_id,
                    c.chunk_index AS chunk_index,
                    c.heading AS heading,
                    c.content AS content,
                    p.title AS title,
                    p.url AS url,
                    p.local_path AS local_path,
                    p.fetched_at AS fetched_at
                FROM chunks c
                JOIN pages p ON p.id = c.page_id
                WHERE c.id = ?
                """,
                (chunk_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Unknown docs chunk id: {chunk_id}")
        return dict(row)

    def get_page(self, page_id: int) -> dict[str, Any]:
        """Return a full synced page by id."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    source_id,
                    title,
                    url,
                    local_path,
                    fetched_at,
                    text_content
                FROM pages
                WHERE id = ?
                """,
                (page_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Unknown docs page id: {page_id}")
        result = dict(row)
        result["chunk_ids"] = self._get_page_chunk_ids(page_id)
        return result

    def _get_page_chunk_ids(self, page_id: int) -> list[int]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id FROM chunks WHERE page_id = ? ORDER BY chunk_index",
                (page_id,),
            ).fetchall()
        return [row["id"] for row in rows]

    def dumps_status(self) -> str:
        """Return the index status as JSON text."""
        return json.dumps(self.get_status(), indent=2)
