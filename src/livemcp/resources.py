"""Controller-oriented MCP resources for inspecting Ableton state."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .docs import DocsIndex
from .connection import get_connection
from .tools import session


def _read_track_info(track_index: int) -> dict[str, Any]:
    return get_connection().send_command("get_track_info", {"track_index": track_index})


def _read_scene_info(scene_index: int) -> session.SceneInfo:
    return get_connection().send_command("get_scene_info", {"scene_index": scene_index})


def _read_scene_clips(scene_index: int) -> dict[str, Any]:
    return get_connection().send_command("get_scene_clips", {"scene_index": scene_index})


def _read_device_display_values(track_index: int, device_index: int) -> dict[str, Any]:
    return get_connection().send_command(
        "get_device_display_values",
        {"track_index": track_index, "device_index": device_index},
    )


def _read_docs_status() -> dict[str, Any]:
    return DocsIndex().get_status()


def _read_docs_chunk(chunk_id: int) -> dict[str, Any]:
    return DocsIndex().get_chunk(chunk_id)


def _read_docs_page(page_id: int) -> dict[str, Any]:
    return DocsIndex().get_page(page_id)


def register_resources(mcp: FastMCP) -> None:
    """Register the controller-oriented MCP resources."""

    @mcp.resource(
        "live://status",
        name="livemcp_status_resource",
        title="LiveMCP Status",
        description="Combined local install state, remote-script reachability, and transport warnings.",
        mime_type="application/json",
    )
    def livemcp_status() -> session.LiveMCPStatus:
        return session.get_livemcp_status()

    @mcp.resource(
        "live://session/current",
        name="current_session_resource",
        title="Current Session",
        description="Current Ableton session transport and timing state.",
        mime_type="application/json",
    )
    def current_session() -> session.SessionInfo:
        return session.get_session_info()

    @mcp.resource(
        "live://song/time",
        name="song_time_resource",
        title="Song Time",
        description="Current song playhead position and undo/redo state.",
        mime_type="application/json",
    )
    def song_time() -> session.SongTimeInfo:
        return session.get_song_time()

    @mcp.resource(
        "live://view/current",
        name="current_view_resource",
        title="Current View",
        description="Current Ableton UI view state, including visible views and follow-song state.",
        mime_type="application/json",
    )
    def current_view() -> session.ViewStateInfo:
        return session.get_view_state()

    @mcp.resource(
        "live://selection/track",
        name="selected_track_resource",
        title="Selected Track",
        description="Currently selected Ableton track.",
        mime_type="application/json",
    )
    def selected_track() -> session.SelectedTrackInfo:
        return session.get_selected_track()

    @mcp.resource(
        "live://selection/scene",
        name="selected_scene_resource",
        title="Selected Scene",
        description="Currently selected Ableton scene.",
        mime_type="application/json",
    )
    def selected_scene() -> session.SelectedSceneInfo:
        return session.get_selected_scene()

    @mcp.resource(
        "live://selection/device",
        name="selected_device_resource",
        title="Selected Device",
        description="Currently selected device on the selected track.",
        mime_type="application/json",
    )
    def selected_device() -> session.SelectedDeviceInfo:
        return session.get_selected_device()

    @mcp.resource(
        "live://application/dialog",
        name="application_dialog_resource",
        title="Application Dialog",
        description="Current Ableton application dialog state.",
        mime_type="application/json",
    )
    def application_dialog() -> session.ApplicationDialogInfo:
        return session.get_application_dialog()

    @mcp.resource(
        "live://track/{track_index}",
        name="track_resource",
        title="Track",
        description="Detailed state for a specific Ableton track.",
        mime_type="application/json",
    )
    def track(track_index: int) -> dict[str, Any]:
        return _read_track_info(track_index)

    @mcp.resource(
        "live://scene/{scene_index}",
        name="scene_resource",
        title="Scene",
        description="Detailed state for a specific Ableton scene.",
        mime_type="application/json",
    )
    def scene(scene_index: int) -> session.SceneInfo:
        return _read_scene_info(scene_index)

    @mcp.resource(
        "live://scene/{scene_index}/clips",
        name="scene_clips_resource",
        title="Scene Clips",
        description="Clip-slot state for every track in a specific scene.",
        mime_type="application/json",
    )
    def scene_clips(scene_index: int) -> dict[str, Any]:
        return _read_scene_clips(scene_index)

    @mcp.resource(
        "live://device/{track_index}/{device_index}",
        name="device_resource",
        title="Device",
        description="Detailed device parameters with display values for a specific device.",
        mime_type="application/json",
    )
    def device(track_index: int, device_index: int) -> dict[str, Any]:
        return _read_device_display_values(track_index, device_index)

    @mcp.resource(
        "docs://status",
        name="docs_status_resource",
        title="Docs Status",
        description="Status of the local Ableton and Max docs index.",
        mime_type="application/json",
    )
    def docs_status() -> dict[str, Any]:
        return _read_docs_status()

    @mcp.resource(
        "docs://chunk/{chunk_id}",
        name="docs_chunk_resource",
        title="Docs Chunk",
        description="A single chunk from the local synced docs index.",
        mime_type="application/json",
    )
    def docs_chunk(chunk_id: int) -> dict[str, Any]:
        return _read_docs_chunk(chunk_id)

    @mcp.resource(
        "docs://page/{page_id}",
        name="docs_page_resource",
        title="Docs Page",
        description="A full page from the local synced docs index.",
        mime_type="application/json",
    )
    def docs_page(page_id: int) -> dict[str, Any]:
        return _read_docs_page(page_id)
