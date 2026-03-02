"""Session-level tools: tempo, transport, time signature."""

import json

from ..connection import get_connection


def get_session_info() -> str:
    """Get the current Ableton Live session state.

    Returns tempo, time signature, track count, return track count,
    master track info, playback state, and loop settings.
    """
    result = get_connection().send_command("get_session_info", {})
    return json.dumps(result)


def set_tempo(tempo: float) -> str:
    """Set the session tempo in BPM.

    Args:
        tempo: Tempo value between 20 and 999 BPM.
    """
    result = get_connection().send_command("set_tempo", {"tempo": tempo})
    return json.dumps(result)


def start_playback() -> str:
    """Start playing the Ableton Live session."""
    result = get_connection().send_command("start_playback", {})
    return json.dumps(result)


def stop_playback() -> str:
    """Stop playing the Ableton Live session."""
    result = get_connection().send_command("stop_playback", {})
    return json.dumps(result)


TOOLS = [get_session_info, set_tempo, start_playback, stop_playback]
