"""Arrangement view tools: clips, overdub, back to arrangement."""

import json

from ..connection import get_connection


def get_arrangement_clips(track_index: int) -> str:
    """Get all clips in the arrangement view for a track.

    Args:
        track_index: Zero-based index of the track.
    """
    result = get_connection().send_command("get_arrangement_clips", {
        "track_index": track_index,
    })
    return json.dumps(result)


def get_arrangement_length() -> str:
    """Get the total arrangement length in beats.

    Returns the time position of the last event in the arrangement.
    """
    result = get_connection().send_command("get_arrangement_length", {})
    return json.dumps(result)


def get_arrangement_overdub() -> str:
    """Get the current arrangement overdub state.

    Returns whether arrangement overdub is enabled (recording merges with existing clips).
    """
    result = get_connection().send_command("get_arrangement_overdub", {})
    return json.dumps(result)


def create_arrangement_midi_clip(track_index: int, start_time: float, length: float) -> str:
    """Create a new empty MIDI clip in the arrangement view.

    Args:
        track_index: Zero-based index of the track (must be a MIDI track).
        start_time: Start position of the clip in beats.
        length: Length of the clip in beats.
    """
    result = get_connection().send_command("create_arrangement_midi_clip", {
        "track_index": track_index,
        "start_time": start_time,
        "length": length,
    })
    return json.dumps(result)


def create_arrangement_audio_clip(track_index: int, file_path: str, position: float) -> str:
    """Create an audio clip in the arrangement view from an audio file.

    Args:
        track_index: Zero-based index of the track (must be an audio track).
        file_path: Absolute path to the audio file to load.
        position: Position in beats where the clip should be placed.
    """
    result = get_connection().send_command("create_arrangement_audio_clip", {
        "track_index": track_index,
        "file_path": file_path,
        "position": position,
    })
    return json.dumps(result)


def duplicate_to_arrangement(track_index: int, clip_index: int, time: float) -> str:
    """Duplicate a session clip to the arrangement view.

    Args:
        track_index: Zero-based index of the track containing the session clip.
        clip_index: Zero-based index of the clip slot in session view.
        time: Position in beats where the duplicated clip should be placed in the arrangement.
    """
    result = get_connection().send_command("duplicate_to_arrangement", {
        "track_index": track_index,
        "clip_index": clip_index,
        "time": time,
    })
    return json.dumps(result)


def delete_arrangement_clip(track_index: int, arrangement_clip_index: int) -> str:
    """Delete a clip from the arrangement view.

    Args:
        track_index: Zero-based index of the track.
        arrangement_clip_index: Index of the clip in the track's arrangement_clips list.
    """
    result = get_connection().send_command("delete_arrangement_clip", {
        "track_index": track_index,
        "arrangement_clip_index": arrangement_clip_index,
    })
    return json.dumps(result)


def set_arrangement_overdub(enabled: bool) -> str:
    """Set the arrangement overdub state.

    When enabled, recording in arrangement view merges new notes with existing clip content
    instead of replacing it.

    Args:
        enabled: True to enable overdub, False to disable.
    """
    result = get_connection().send_command("set_arrangement_overdub", {
        "enabled": enabled,
    })
    return json.dumps(result)


def trigger_back_to_arrangement() -> str:
    """Trigger back to arrangement.

    Deactivates all session clip playback and returns to the arrangement view playback.
    Equivalent to clicking the 'Back to Arrangement' button in Ableton.
    """
    result = get_connection().send_command("trigger_back_to_arrangement", {})
    return json.dumps(result)


TOOLS = [
    get_arrangement_clips,
    get_arrangement_length,
    get_arrangement_overdub,
    create_arrangement_midi_clip,
    create_arrangement_audio_clip,
    duplicate_to_arrangement,
    delete_arrangement_clip,
    set_arrangement_overdub,
    trigger_back_to_arrangement,
]
