"""Documentation source catalog for local sync."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocSource:
    """A bounded crawl definition for a documentation corpus."""

    source_id: str
    label: str
    description: str
    seed_urls: tuple[str, ...]
    allowed_prefixes: tuple[str, ...]
    max_pages: int

    def matches(self, url: str) -> bool:
        return any(url.startswith(prefix) for prefix in self.allowed_prefixes)


DOC_SOURCES: dict[str, DocSource] = {
    "ableton-live-manual-12": DocSource(
        source_id="ableton-live-manual-12",
        label="Ableton Live Manual 12",
        description="Official Ableton Live 12 reference manual pages.",
        seed_urls=("https://www.ableton.com/en/live-manual/12/",),
        allowed_prefixes=("https://www.ableton.com/en/live-manual/12/",),
        max_pages=400,
    ),
    "cycling74-max-docs": DocSource(
        source_id="cycling74-max-docs",
        label="Cycling '74 Max Docs",
        description=(
            "Official Max, Max for Live, Live Object Model, JavaScript, and Node for Max docs."
        ),
        seed_urls=(
            "https://docs.cycling74.com/api/latest/max8/vignettes/live_api_overview/",
            "https://docs.cycling74.com/apiref/lom/",
            "https://docs.cycling74.com/apiref/js/",
            "https://docs.cycling74.com/apiref/nodeformax/",
            "https://docs.cycling74.com/reference/live.object",
            "https://docs.cycling74.com/reference/live.path",
            "https://docs.cycling74.com/reference/live.observer",
            "https://docs.cycling74.com/reference/live.remote~",
            "https://docs.cycling74.com/reference/",
        ),
        allowed_prefixes=(
            "https://docs.cycling74.com/api/latest/max8/",
            "https://docs.cycling74.com/apiref/",
            "https://docs.cycling74.com/reference/",
        ),
        max_pages=2500,
    ),
}


def get_doc_source(source_id: str) -> DocSource:
    """Return a configured documentation source or raise ValueError."""
    try:
        return DOC_SOURCES[source_id]
    except KeyError as exc:
        raise ValueError(f"Unknown docs source: {source_id}") from exc


def list_doc_sources() -> list[DocSource]:
    """Return all configured documentation sources."""
    return list(DOC_SOURCES.values())
