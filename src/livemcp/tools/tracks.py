"""Track tools: info, creation, naming, deletion."""

import json

from ..connection import get_connection


def get_track_info(track_index: int) -> str:
    """Get detailed information about a specific track.

    Returns the track name, type, mute/solo/arm state, volume, pan,
    list of clip slots with clip info, and list of devices.

    Args:
        track_index: Zero-based index of the track.
    """
    result = get_connection().send_command("get_track_info", {"track_index": track_index})
    return json.dumps(result)


def create_midi_track(index: int = -1) -> str:
    """Create a new MIDI track in the session.

    Args:
        index: Position to insert the track. Use -1 to append at the end.
    """
    result = get_connection().send_command("create_midi_track", {"index": index})
    return json.dumps(result)


def create_audio_track(index: int = -1) -> str:
    """Create a new audio track in the session.

    Args:
        index: Position to insert the track. Use -1 to append at the end.
    """
    result = get_connection().send_command("create_audio_track", {"index": index})
    return json.dumps(result)


def set_track_name(track_index: int, name: str) -> str:
    """Set the name of a track.

    Args:
        track_index: Zero-based index of the track.
        name: New name for the track.
    """
    result = get_connection().send_command("set_track_name", {
        "track_index": track_index,
        "name": name,
    })
    return json.dumps(result)


def delete_track(track_index: int) -> str:
    """Delete a track from the session.

    Args:
        track_index: Zero-based index of the track to delete.
    """
    result = get_connection().send_command("delete_track", {"track_index": track_index})
    return json.dumps(result)


def get_return_tracks() -> str:
    """Get information about all return tracks in the session.

    Returns a list of return tracks with name, mute, solo, volume, and pan.
    """
    result = get_connection().send_command("get_return_tracks", {})
    return json.dumps(result)


TOOLS = [
    get_track_info,
    create_midi_track,
    create_audio_track,
    set_track_name,
    delete_track,
    get_return_tracks,
]
