"""Clip tools: MIDI notes, clip management, scenes."""

import json

from ..connection import get_connection


def create_clip(track_index: int, clip_index: int, length: float = 4.0) -> str:
    """Create a new MIDI clip in a track's clip slot.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        length: Length of the clip in beats (default 4.0 = one bar at 4/4).
    """
    result = get_connection().send_command("create_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
        "length": length,
    })
    return json.dumps(result)


def set_clip_name(track_index: int, clip_index: int, name: str) -> str:
    """Set the name of a clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        name: New name for the clip.
    """
    result = get_connection().send_command("set_clip_name", {
        "track_index": track_index,
        "clip_index": clip_index,
        "name": name,
    })
    return json.dumps(result)


def delete_clip(track_index: int, clip_index: int) -> str:
    """Delete a clip from a clip slot.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("delete_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def add_notes_to_clip(track_index: int, clip_index: int, notes: list) -> str:
    """Add MIDI notes to an existing clip.

    Each note is a dict with: pitch (0-127 MIDI note number), start_time (beat position),
    duration (in beats), velocity (0-127), and mute (boolean).

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        notes: List of note dicts, each with pitch, start_time, duration, velocity, mute.
    """
    result = get_connection().send_command("add_notes_to_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
        "notes": notes,
    })
    return json.dumps(result)


def get_notes_from_clip(track_index: int, clip_index: int) -> str:
    """Read all MIDI notes from a clip.

    Returns a list of notes with pitch, start_time, duration, velocity, and mute.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("get_notes_from_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def fire_clip(track_index: int, clip_index: int) -> str:
    """Start playing a clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("fire_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def stop_clip(track_index: int, clip_index: int) -> str:
    """Stop playing a clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("stop_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def fire_scene(scene_index: int) -> str:
    """Fire (launch) a scene, triggering all clips in that row.

    Args:
        scene_index: Zero-based index of the scene.
    """
    result = get_connection().send_command("fire_scene", {"scene_index": scene_index})
    return json.dumps(result)


def create_scene(index: int = -1) -> str:
    """Create a new scene in the session.

    Args:
        index: Position to insert the scene. Use -1 to append at the end.
    """
    result = get_connection().send_command("create_scene", {"index": index})
    return json.dumps(result)


def get_scene_info(scene_index: int) -> str:
    """Get information about a specific scene.

    Args:
        scene_index: Zero-based index of the scene.
    """
    result = get_connection().send_command("get_scene_info", {"scene_index": scene_index})
    return json.dumps(result)


TOOLS = [
    create_clip,
    set_clip_name,
    delete_clip,
    add_notes_to_clip,
    get_notes_from_clip,
    fire_clip,
    stop_clip,
    fire_scene,
    create_scene,
    get_scene_info,
]
