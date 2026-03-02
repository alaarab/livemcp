"""Mixer tools: volume, pan, mute, solo, arm, sends."""

import json

from ..connection import get_connection


def set_track_volume(track_index: int, volume: float) -> str:
    """Set the volume of a track.

    Args:
        track_index: Zero-based index of the track.
        volume: Volume level (0.0 = -inf dB, 0.85 = 0 dB, 1.0 = +6 dB).
    """
    result = get_connection().send_command("set_track_volume", {
        "track_index": track_index,
        "volume": volume,
    })
    return json.dumps(result)


def set_track_pan(track_index: int, pan: float) -> str:
    """Set the panning of a track.

    Args:
        track_index: Zero-based index of the track.
        pan: Pan value from -1.0 (full left) to 1.0 (full right). 0.0 is center.
    """
    result = get_connection().send_command("set_track_pan", {
        "track_index": track_index,
        "pan": pan,
    })
    return json.dumps(result)


def set_track_mute(track_index: int, mute: bool) -> str:
    """Set the mute state of a track.

    Args:
        track_index: Zero-based index of the track.
        mute: True to mute, False to unmute.
    """
    result = get_connection().send_command("set_track_mute", {
        "track_index": track_index,
        "mute": mute,
    })
    return json.dumps(result)


def set_track_solo(track_index: int, solo: bool) -> str:
    """Set the solo state of a track.

    Args:
        track_index: Zero-based index of the track.
        solo: True to solo, False to unsolo.
    """
    result = get_connection().send_command("set_track_solo", {
        "track_index": track_index,
        "solo": solo,
    })
    return json.dumps(result)


def set_track_arm(track_index: int, arm: bool) -> str:
    """Set the record arm state of a track.

    Args:
        track_index: Zero-based index of the track.
        arm: True to arm for recording, False to disarm.
    """
    result = get_connection().send_command("set_track_arm", {
        "track_index": track_index,
        "arm": arm,
    })
    return json.dumps(result)


def set_track_send(track_index: int, send_index: int, value: float) -> str:
    """Set the send level from a track to a return track.

    Args:
        track_index: Zero-based index of the source track.
        send_index: Zero-based index of the send (corresponds to return track order).
        value: Send level from 0.0 (off) to 1.0 (full).
    """
    result = get_connection().send_command("set_track_send", {
        "track_index": track_index,
        "send_index": send_index,
        "value": value,
    })
    return json.dumps(result)


def get_mixer_state() -> str:
    """Get the mixer state of all tracks.

    Returns volume, pan, mute, solo, and arm state for every track in the session.
    """
    result = get_connection().send_command("get_mixer_state", {})
    return json.dumps(result)


def get_master_mixer_state() -> str:
    """Get the mixer state of the master track.

    Returns volume, pan, crossfader value, and a list of devices on the master track.
    """
    result = get_connection().send_command("get_master_mixer_state", {})
    return json.dumps(result)


def set_master_volume(volume: float) -> str:
    """Set the volume of the master track.

    Args:
        volume: Volume level (0.0 = -inf dB, 0.85 = 0 dB, 1.0 = +6 dB).
    """
    result = get_connection().send_command("set_master_volume", {
        "volume": volume,
    })
    return json.dumps(result)


def set_master_pan(pan: float) -> str:
    """Set the panning of the master track.

    Args:
        pan: Pan value from -1.0 (full left) to 1.0 (full right). 0.0 is center.
    """
    result = get_connection().send_command("set_master_pan", {
        "pan": pan,
    })
    return json.dumps(result)


def set_crossfade_assign(track_index: int, assignment: int) -> str:
    """Set the crossfade assignment of a track.

    Args:
        track_index: Zero-based index of the track.
        assignment: 0 = no crossfade assignment, 1 = assign to A, 2 = assign to B.
    """
    result = get_connection().send_command("set_crossfade_assign", {
        "track_index": track_index,
        "assignment": assignment,
    })
    return json.dumps(result)


def get_master_output_meter() -> str:
    """Get the current output meter levels for the master track.

    Returns output_meter_level (peak), output_meter_left, and output_meter_right.
    Values are in the range 0.0 to 1.0.
    """
    result = get_connection().send_command("get_master_output_meter", {})
    return json.dumps(result)


def get_return_track_output_meter(return_index: int) -> str:
    """Get the current output meter levels for a return track.

    Args:
        return_index: Zero-based index of the return track.

    Returns return_index, name, output_meter_level, output_meter_left, and output_meter_right.
    Values are in the range 0.0 to 1.0.
    """
    result = get_connection().send_command("get_return_track_output_meter", {
        "return_index": return_index,
    })
    return json.dumps(result)


def get_all_track_meters() -> str:
    """Get output meter levels for all tracks and the master track.

    Returns a dict with 'tracks' (list of per-track meter data) and 'master' meter data.
    Each entry includes output_meter_level, output_meter_left, and output_meter_right (0.0-1.0).
    """
    result = get_connection().send_command("get_all_track_meters", {})
    return json.dumps(result)


TOOLS = [
    set_track_volume,
    set_track_pan,
    set_track_mute,
    set_track_solo,
    set_track_arm,
    set_track_send,
    get_mixer_state,
    get_master_mixer_state,
    set_master_volume,
    set_master_pan,
    set_crossfade_assign,
    get_master_output_meter,
    get_return_track_output_meter,
    get_all_track_meters,
]
