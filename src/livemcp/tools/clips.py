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


def remove_notes_from_clip(
    track_index: int,
    clip_index: int,
    from_pitch: int = 0,
    pitch_span: int = 128,
    from_time: float = 0.0,
    time_span: float = None,
) -> str:
    """Remove MIDI notes from a clip within a pitch and time range.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        from_pitch: Starting pitch (0-127, default 0).
        pitch_span: Number of pitches to span (default 128 = all).
        from_time: Start time in beats (default 0.0).
        time_span: Time span in beats. If None, uses clip length.
    """
    params = {
        "track_index": track_index,
        "clip_index": clip_index,
        "from_pitch": from_pitch,
        "pitch_span": pitch_span,
        "from_time": from_time,
    }
    if time_span is not None:
        params["time_span"] = time_span
    result = get_connection().send_command("remove_notes_from_clip", params)
    return json.dumps(result)


def clear_clip_notes(track_index: int, clip_index: int) -> str:
    """Remove all MIDI notes from a clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("clear_clip_notes", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def set_clip_loop(
    track_index: int,
    clip_index: int,
    looping: bool = None,
    loop_start: float = None,
    loop_end: float = None,
    start_marker: float = None,
    end_marker: float = None,
) -> str:
    """Set clip loop and marker properties.

    All loop parameters are optional; only provided values are changed.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        looping: Enable or disable looping.
        loop_start: Loop start position in beats.
        loop_end: Loop end position in beats.
        start_marker: Start marker position in beats.
        end_marker: End marker position in beats.
    """
    params = {
        "track_index": track_index,
        "clip_index": clip_index,
    }
    if looping is not None:
        params["looping"] = looping
    if loop_start is not None:
        params["loop_start"] = loop_start
    if loop_end is not None:
        params["loop_end"] = loop_end
    if start_marker is not None:
        params["start_marker"] = start_marker
    if end_marker is not None:
        params["end_marker"] = end_marker
    result = get_connection().send_command("set_clip_loop", params)
    return json.dumps(result)


def duplicate_clip(
    track_index: int,
    clip_index: int,
    target_track_index: int,
    target_clip_index: int,
) -> str:
    """Duplicate a clip to another clip slot.

    Args:
        track_index: Zero-based index of the source track.
        clip_index: Zero-based index of the source clip slot.
        target_track_index: Zero-based index of the destination track.
        target_clip_index: Zero-based index of the destination clip slot.
    """
    result = get_connection().send_command("duplicate_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
        "target_track_index": target_track_index,
        "target_clip_index": target_clip_index,
    })
    return json.dumps(result)


def set_clip_color(track_index: int, clip_index: int, color_index: int) -> str:
    """Set the color of a clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        color_index: Ableton color index to set.
    """
    result = get_connection().send_command("set_clip_color", {
        "track_index": track_index,
        "clip_index": clip_index,
        "color_index": color_index,
    })
    return json.dumps(result)


def quantize_clip(
    track_index: int, clip_index: int, grid: int, amount: float = 1.0
) -> str:
    """Quantize notes in a clip to a grid.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        grid: RecordingQuantization enum value (1=1/4, 2=1/8, 3=1/8T, 4=1/8+T,
              5=1/16, 6=1/16T, 7=1/16+T, 8=1/32).
        amount: Quantize strength from 0.0 to 1.0 (default 1.0 = full quantize).
    """
    result = get_connection().send_command("quantize_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
        "grid": grid,
        "amount": amount,
    })
    return json.dumps(result)


def duplicate_clip_loop(track_index: int, clip_index: int) -> str:
    """Duplicate the loop content of a clip, doubling its length.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("duplicate_clip_loop", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def crop_clip(track_index: int, clip_index: int) -> str:
    """Crop a clip to its loop boundaries.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("crop_clip", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def set_clip_muted(track_index: int, clip_index: int, muted: bool) -> str:
    """Set whether a clip is muted (deactivated).

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        muted: True to mute, False to unmute.
    """
    result = get_connection().send_command("set_clip_muted", {
        "track_index": track_index,
        "clip_index": clip_index,
        "muted": muted,
    })
    return json.dumps(result)


def set_clip_gain(track_index: int, clip_index: int, gain: float) -> str:
    """Set the gain of an audio clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        gain: Gain value to set.
    """
    result = get_connection().send_command("set_clip_gain", {
        "track_index": track_index,
        "clip_index": clip_index,
        "gain": gain,
    })
    return json.dumps(result)


def set_clip_pitch(
    track_index: int, clip_index: int, coarse: int = None, fine: float = None
) -> str:
    """Set the pitch transposition of an audio clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        coarse: Coarse pitch in semitones (-48 to 48).
        fine: Fine pitch in cents (-50.0 to 50.0).
    """
    params = {
        "track_index": track_index,
        "clip_index": clip_index,
    }
    if coarse is not None:
        params["coarse"] = coarse
    if fine is not None:
        params["fine"] = fine
    result = get_connection().send_command("set_clip_pitch", params)
    return json.dumps(result)


def set_clip_launch_mode(track_index: int, clip_index: int, mode: int) -> str:
    """Set the launch mode of a clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        mode: Launch mode (0=Trigger, 1=Gate, 2=Toggle, 3=Repeat).
    """
    result = get_connection().send_command("set_clip_launch_mode", {
        "track_index": track_index,
        "clip_index": clip_index,
        "mode": mode,
    })
    return json.dumps(result)


def set_clip_warp_mode(track_index: int, clip_index: int, warp_mode: int) -> str:
    """Set the warp mode of an audio clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        warp_mode: Warp mode index to set.
    """
    result = get_connection().send_command("set_clip_warp_mode", {
        "track_index": track_index,
        "clip_index": clip_index,
        "warp_mode": warp_mode,
    })
    return json.dumps(result)


def get_clip_envelope(
    track_index: int,
    clip_index: int,
    device_index: int,
    param_index: int,
    num_steps: int = 16,
) -> str:
    """Sample the automation envelope for a device parameter in a Session clip.

    The Ableton API does not expose individual breakpoints, so this samples
    the envelope value at evenly-spaced time positions across the clip.
    Returns envelope_exists=False if no envelope is set for the parameter.
    Only works for Session clips (not Arrangement clips).

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        device_index: Zero-based index of the device on the track.
        param_index: Zero-based index of the parameter on the device.
        num_steps: Number of sample points across the clip (2-128, default 16).
    """
    result = get_connection().send_command("get_clip_envelope", {
        "track_index": track_index,
        "clip_index": clip_index,
        "device_index": device_index,
        "param_index": param_index,
        "num_steps": num_steps,
    })
    return json.dumps(result)


def insert_clip_envelope_step(
    track_index: int,
    clip_index: int,
    device_index: int,
    param_index: int,
    time: float,
    value: float,
    curve: float = 0.0,
) -> str:
    """Insert an automation breakpoint into a clip's parameter envelope.

    Writes a single automation point at the given time with the given value.
    Creates the envelope if it does not exist yet. Only works for Session clips.
    Note: Arrangement clips will return an error.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        device_index: Zero-based index of the device on the track.
        param_index: Zero-based index of the parameter on the device.
        time: Time position in beats to insert the automation point.
        value: Automation value to set at the given time.
        curve: Curve shape (0.0 = linear, default 0.0).
    """
    result = get_connection().send_command("insert_clip_envelope_step", {
        "track_index": track_index,
        "clip_index": clip_index,
        "device_index": device_index,
        "param_index": param_index,
        "time": time,
        "value": value,
        "curve": curve,
    })
    return json.dumps(result)


def clear_clip_envelope(
    track_index: int,
    clip_index: int,
    device_index: int,
    param_index: int,
) -> str:
    """Clear the automation envelope for a specific device parameter in a clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        device_index: Zero-based index of the device on the track.
        param_index: Zero-based index of the parameter on the device.
    """
    result = get_connection().send_command("clear_clip_envelope", {
        "track_index": track_index,
        "clip_index": clip_index,
        "device_index": device_index,
        "param_index": param_index,
    })
    return json.dumps(result)


def clear_all_clip_envelopes(track_index: int, clip_index: int) -> str:
    """Clear all automation envelopes in a clip.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("clear_all_clip_envelopes", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def get_notes_extended(track_index: int, clip_index: int) -> str:
    """Read all MIDI notes from a clip with extended properties.

    Returns notes with pitch, start_time, duration, velocity, mute,
    probability, velocity_deviation, and release_velocity.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("get_notes_extended", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def add_notes_extended(track_index: int, clip_index: int, notes: list) -> str:
    """Add MIDI notes with extended properties to a clip.

    Each note is a dict with: pitch (0-127), start_time (beat position),
    duration (in beats), velocity (0-127), and optionally probability (0.0-1.0),
    velocity_deviation (-127 to 127), release_velocity (0-127), mute (boolean).

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        notes: List of note dicts with pitch, start_time, duration, velocity,
               and optional probability, velocity_deviation, release_velocity, mute.
    """
    result = get_connection().send_command("add_notes_extended", {
        "track_index": track_index,
        "clip_index": clip_index,
        "notes": notes,
    })
    return json.dumps(result)


def modify_notes(track_index: int, clip_index: int, modifications: list) -> str:
    """Modify properties of existing MIDI notes in a clip.

    Each modification dict must include pitch and start_time to identify the note,
    plus any properties to change: velocity, probability, velocity_deviation,
    release_velocity, mute.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        modifications: List of modification dicts, each with pitch, start_time,
                       and properties to modify.
    """
    result = get_connection().send_command("modify_notes", {
        "track_index": track_index,
        "clip_index": clip_index,
        "modifications": modifications,
    })
    return json.dumps(result)


def get_clip_properties(track_index: int, clip_index: int) -> str:
    """Get comprehensive properties of a clip.

    Returns name, color, color_index, is_audio_clip, is_midi_clip, length,
    start_marker, end_marker, looping, loop_start, loop_end, launch_mode,
    launch_quantization, velocity_amount, muted, and has_groove (if available).
    For audio clips also returns file_path, ram_mode, gain, and gain_display_string.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("get_clip_properties", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def set_clip_ram_mode(track_index: int, clip_index: int, ram_mode: bool) -> str:
    """Set RAM mode for an audio clip.

    When enabled, the clip's audio is loaded into RAM for playback.
    Only available for audio clips.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        ram_mode: True to enable RAM mode, False to disable.
    """
    result = get_connection().send_command("set_clip_ram_mode", {
        "track_index": track_index,
        "clip_index": clip_index,
        "ram_mode": ram_mode,
    })
    return json.dumps(result)


def set_clip_velocity_amount(track_index: int, clip_index: int, velocity_amount: float) -> str:
    """Set the velocity-to-volume amount for a clip.

    Controls how much note velocity affects clip volume.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        velocity_amount: Velocity-to-volume amount (0.0 to 1.0).
    """
    result = get_connection().send_command("set_clip_velocity_amount", {
        "track_index": track_index,
        "clip_index": clip_index,
        "velocity_amount": velocity_amount,
    })
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
    remove_notes_from_clip,
    clear_clip_notes,
    set_clip_loop,
    duplicate_clip,
    set_clip_color,
    quantize_clip,
    duplicate_clip_loop,
    crop_clip,
    set_clip_muted,
    set_clip_gain,
    set_clip_pitch,
    set_clip_launch_mode,
    set_clip_warp_mode,
    get_clip_envelope,
    insert_clip_envelope_step,
    clear_clip_envelope,
    clear_all_clip_envelopes,
    get_notes_extended,
    add_notes_extended,
    modify_notes,
    get_clip_properties,
    set_clip_ram_mode,
    set_clip_velocity_amount,
]
