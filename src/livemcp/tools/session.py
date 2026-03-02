"""Session-level tools: tempo, transport, time signature."""

import json
from typing import Optional

from ..connection import get_connection


def get_session_info() -> str:
    """Get the current Ableton Live session state.

    Returns tempo, time signature, track count, return track count,
    master track info, playback state, and loop settings.
    """
    result = get_connection().send_command("get_session_info", {})
    return json.dumps(result)


def get_song_time() -> str:
    """Get the current song time position and undo/redo availability.

    Returns current_song_time (in beats), can_undo, and can_redo.
    """
    result = get_connection().send_command("get_song_time", {})
    return json.dumps(result)


def get_cue_points() -> str:
    """Get all cue points (locators) in the song.

    Returns a list of cue points with index, name, and time.
    """
    result = get_connection().send_command("get_cue_points", {})
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


def undo() -> str:
    """Undo the last action in Ableton Live."""
    result = get_connection().send_command("undo", {})
    return json.dumps(result)


def redo() -> str:
    """Redo the last undone action in Ableton Live."""
    result = get_connection().send_command("redo", {})
    return json.dumps(result)


def set_time_signature(numerator: int, denominator: int) -> str:
    """Set the song time signature.

    Args:
        numerator: Time signature numerator (e.g., 4 for 4/4).
        denominator: Time signature denominator (e.g., 4 for 4/4).
    """
    result = get_connection().send_command("set_time_signature", {
        "numerator": numerator,
        "denominator": denominator,
    })
    return json.dumps(result)


def set_loop_region(
    loop_on: Optional[bool] = None,
    loop_start: Optional[float] = None,
    loop_length: Optional[float] = None,
) -> str:
    """Set the loop region and on/off state.

    Args:
        loop_on: Enable or disable looping.
        loop_start: Loop start position in beats.
        loop_length: Loop length in beats.
    """
    params = {}
    if loop_on is not None:
        params["loop_on"] = loop_on
    if loop_start is not None:
        params["loop_start"] = loop_start
    if loop_length is not None:
        params["loop_length"] = loop_length
    result = get_connection().send_command("set_loop_region", params)
    return json.dumps(result)


def set_song_time(time: float) -> str:
    """Set the current song time (playhead position) in beats.

    Args:
        time: Position in beats to jump to.
    """
    result = get_connection().send_command("set_song_time", {"time": time})
    return json.dumps(result)


def continue_playing() -> str:
    """Continue playback from the current position without restart."""
    result = get_connection().send_command("continue_playing", {})
    return json.dumps(result)


def stop_all_clips() -> str:
    """Stop all playing clips in the session."""
    result = get_connection().send_command("stop_all_clips", {})
    return json.dumps(result)


def capture_midi() -> str:
    """Capture recently played MIDI notes into a new clip."""
    result = get_connection().send_command("capture_midi", {})
    return json.dumps(result)


def set_metronome(on: bool) -> str:
    """Enable or disable the metronome.

    Args:
        on: True to enable, False to disable.
    """
    result = get_connection().send_command("set_metronome", {"on": on})
    return json.dumps(result)


def set_groove_amount(amount: float) -> str:
    """Set the global groove amount.

    Args:
        amount: Groove amount value (0.0 to 1.0).
    """
    result = get_connection().send_command("set_groove_amount", {"amount": amount})
    return json.dumps(result)


def set_scale(
    root_note: Optional[int] = None,
    scale_name: Optional[str] = None,
) -> str:
    """Set the song scale root note and/or scale name (Live 12+).

    Args:
        root_note: MIDI note number for the root (0=C, 1=C#, ..., 11=B).
        scale_name: Scale name (e.g., 'Major', 'Minor', 'Dorian').
    """
    params = {}
    if root_note is not None:
        params["root_note"] = root_note
    if scale_name is not None:
        params["scale_name"] = scale_name
    result = get_connection().send_command("set_scale", params)
    return json.dumps(result)


def jump_to_next_cue() -> str:
    """Jump to the next cue point (locator)."""
    result = get_connection().send_command("jump_to_next_cue", {})
    return json.dumps(result)


def jump_to_prev_cue() -> str:
    """Jump to the previous cue point (locator)."""
    result = get_connection().send_command("jump_to_prev_cue", {})
    return json.dumps(result)


def jump_to_cue(index: int) -> str:
    """Jump to a specific cue point by index.

    Args:
        index: Zero-based index of the cue point to jump to.
    """
    result = get_connection().send_command("jump_to_cue", {"index": index})
    return json.dumps(result)


def set_midi_recording_quantization(value: int) -> str:
    """Set the MIDI recording quantization.

    Args:
        value: Quantization enum value (0=None, 1=1/4, 2=1/8, 3=1/8T, 4=1/8+T,
               5=1/16, 6=1/16T, 7=1/16+T, 8=1/32).
    """
    result = get_connection().send_command("set_midi_recording_quantization", {"value": value})
    return json.dumps(result)


def set_clip_trigger_quantization(value: int) -> str:
    """Set the clip trigger (launch) quantization.

    Args:
        value: Quantization enum value (0=None, 1=1/8, 2=1/4, 3=1/2, 4=1 Bar,
               5=2 Bars, 6=4 Bars, 7=8 Bars).
    """
    result = get_connection().send_command("set_clip_trigger_quantization", {"value": value})
    return json.dumps(result)


def trigger_record() -> str:
    """Trigger session record in Ableton Live."""
    result = get_connection().send_command("trigger_record", {})
    return json.dumps(result)


def tap_tempo() -> str:
    """Tap tempo to set the BPM by tapping."""
    result = get_connection().send_command("tap_tempo", {})
    return json.dumps(result)


def get_selected_track() -> str:
    """Get information about the currently selected track.

    Returns the index, name, type, mute/solo/arm state, and color of the selected track.
    """
    result = get_connection().send_command("get_selected_track", {})
    return json.dumps(result)


def set_selected_track(track_index: int) -> str:
    """Set the selected track in Ableton Live.

    Args:
        track_index: Zero-based index of the track to select.
    """
    result = get_connection().send_command("set_selected_track", {"track_index": track_index})
    return json.dumps(result)


def get_selected_scene() -> str:
    """Get information about the currently selected scene.

    Returns the index, name, and color of the selected scene.
    """
    result = get_connection().send_command("get_selected_scene", {})
    return json.dumps(result)


def set_selected_scene(scene_index: int) -> str:
    """Set the selected scene in Ableton Live.

    Args:
        scene_index: Zero-based index of the scene to select.
    """
    result = get_connection().send_command("set_selected_scene", {"scene_index": scene_index})
    return json.dumps(result)


def get_scene_properties(scene_index: int) -> str:
    """Get properties of a specific scene.

    Returns the scene name, tempo (-1.0 if not set), color, color_index,
    and (Live 12+) tempo_enabled, time_signature_numerator/denominator/enabled.

    Args:
        scene_index: Zero-based index of the scene.
    """
    result = get_connection().send_command("get_scene_properties", {"scene_index": scene_index})
    return json.dumps(result)


def set_scene_tempo(scene_index: int, tempo: float) -> str:
    """Set the tempo for a specific scene.

    Pass 0 or a negative value to clear the scene tempo (scene will inherit the song tempo).

    Args:
        scene_index: Zero-based index of the scene.
        tempo: Tempo in BPM, or -1.0 to clear.
    """
    result = get_connection().send_command("set_scene_tempo", {
        "scene_index": scene_index,
        "tempo": tempo,
    })
    return json.dumps(result)


def set_scene_time_signature(scene_index: int, numerator: int, denominator: int) -> str:
    """Set the time signature for a specific scene (Live 12+).

    Args:
        scene_index: Zero-based index of the scene.
        numerator: Time signature numerator (e.g., 4 for 4/4).
        denominator: Time signature denominator (e.g., 4 for 4/4).
    """
    result = get_connection().send_command("set_scene_time_signature", {
        "scene_index": scene_index,
        "numerator": numerator,
        "denominator": denominator,
    })
    return json.dumps(result)


def get_application_info() -> str:
    """Get Ableton Live application version info.

    Returns major_version, minor_version, and bugfix_version.
    """
    result = get_connection().send_command("get_application_info", {})
    return json.dumps(result)


def get_record_mode() -> str:
    """Get whether arrangement recording is armed.

    Returns record_mode (True if armed, False otherwise).
    """
    result = get_connection().send_command("get_record_mode", {})
    return json.dumps(result)


def set_record_mode(enabled: bool) -> str:
    """Enable or disable arrangement recording.

    Args:
        enabled: True to arm recording, False to disarm.
    """
    result = get_connection().send_command("set_record_mode", {"enabled": enabled})
    return json.dumps(result)


def capture_and_insert_scene() -> str:
    """Capture currently playing clips into a new scene.

    Creates a new scene containing all currently playing session clips.
    """
    result = get_connection().send_command("capture_and_insert_scene", {})
    return json.dumps(result)


def create_locator() -> str:
    """Create a cue point (locator) at the current playhead position.

    IMPORTANT: You must call set_song_time first to position the playhead
    at the desired location, then call create_locator. The locator is
    always created at the playhead position, not at an arbitrary time.
    """
    result = get_connection().send_command("create_locator", {})
    return json.dumps(result)


def delete_locator(index: int) -> str:
    """Delete a cue point (locator) by index.

    Due to Ableton API limitations, deletion may require two calls:
    1. First call positions the playhead at the cue point's time.
    2. Second call actually deletes the cue point.
    Check the 'deleted' field in the response.

    Args:
        index: Zero-based index of the cue point to delete.
    """
    result = get_connection().send_command("delete_locator", {"index": index})
    return json.dumps(result)


def get_view_state() -> str:
    """Get the current view state in Ableton Live.

    Returns the selected track, detail clip (if any), draw mode, and follow song state.
    """
    result = get_connection().send_command("get_view_state", {})
    return json.dumps(result)


def set_follow_song(enabled: bool) -> str:
    """Enable or disable Follow Song mode (auto-scroll to follow playhead).

    Args:
        enabled: True to enable, False to disable.
    """
    result = get_connection().send_command("set_follow_song", {"enabled": enabled})
    return json.dumps(result)


def set_draw_mode(enabled: bool) -> str:
    """Enable or disable Draw Mode for editing in Ableton Live.

    Args:
        enabled: True to enable, False to disable.
    """
    result = get_connection().send_command("set_draw_mode", {"enabled": enabled})
    return json.dumps(result)


def select_clip_in_detail(track_index: int, clip_index: int) -> str:
    """Select a clip and show it in the Detail View.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("select_clip_in_detail", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def get_punch_state() -> str:
    """Get the punch in/out state.

    Returns whether punch_in and punch_out are enabled.
    """
    result = get_connection().send_command("get_punch_state", {})
    return json.dumps(result)


def set_punch_in(enabled: bool) -> str:
    """Enable or disable punch in for recording.

    Args:
        enabled: True to enable punch in, False to disable.
    """
    result = get_connection().send_command("set_punch_in", {"enabled": enabled})
    return json.dumps(result)


def set_punch_out(enabled: bool) -> str:
    """Enable or disable punch out for recording.

    Args:
        enabled: True to enable punch out, False to disable.
    """
    result = get_connection().send_command("set_punch_out", {"enabled": enabled})
    return json.dumps(result)


def re_enable_automation() -> str:
    """Re-enable automation that was overridden by manual parameter changes.

    When you manually adjust an automated parameter, the automation is
    overridden. This re-enables all overridden automation.
    """
    result = get_connection().send_command("re_enable_automation", {})
    return json.dumps(result)


def get_session_automation_record() -> str:
    """Get whether session automation recording is enabled.

    Returns session_automation_record (True if enabled).
    """
    result = get_connection().send_command("get_session_automation_record", {})
    return json.dumps(result)


def set_session_automation_record(enabled: bool) -> str:
    """Enable or disable session automation recording.

    When enabled, parameter changes during playback are recorded as automation.

    Args:
        enabled: True to enable, False to disable.
    """
    result = get_connection().send_command("set_session_automation_record", {"enabled": enabled})
    return json.dumps(result)


def show_message(message: str) -> str:
    """Display a message in the Ableton Live status bar.

    Args:
        message: Text to display in the status bar.
    """
    result = get_connection().send_command("show_message", {"message": message})
    return json.dumps(result)


def get_session_metadata() -> str:
    """Get session metadata: modified state, current song time, song length, and CPU load.

    Returns is_modified, current_song_time (beats), song_length (beats),
    and current_cpu_load (if available).
    """
    result = get_connection().send_command("get_session_metadata", {})
    return json.dumps(result)


def get_song_smpte_time() -> str:
    """Get the current song time in SMPTE (timecode) format.

    Returns hours, minutes, seconds, and frames.
    """
    result = get_connection().send_command("get_song_smpte_time", {})
    return json.dumps(result)


def get_scene_info(scene_index: int) -> str:
    """Get detailed information about a specific scene.

    Returns the scene name, color, tempo (if tempo_enabled), time signature
    (if available), is_empty flag (if available), and clip_count across all tracks.

    Args:
        scene_index: Zero-based index of the scene.
    """
    result = get_connection().send_command("get_scene_info", {"scene_index": scene_index})
    return json.dumps(result)


def get_scene_clips(scene_index: int) -> str:
    """Get all clips in a scene across all tracks.

    Returns clip status for every track at the given scene index, including
    track name, whether a clip is present, clip name and color, and
    playing/recording/triggered state.

    Args:
        scene_index: Zero-based index of the scene.
    """
    result = get_connection().send_command("get_scene_clips", {"scene_index": scene_index})
    return json.dumps(result)


TOOLS = [
    get_session_info,
    get_song_time,
    get_cue_points,
    set_tempo,
    start_playback,
    stop_playback,
    undo,
    redo,
    set_time_signature,
    set_loop_region,
    set_song_time,
    continue_playing,
    stop_all_clips,
    capture_midi,
    set_metronome,
    set_groove_amount,
    set_scale,
    jump_to_next_cue,
    jump_to_prev_cue,
    jump_to_cue,
    set_midi_recording_quantization,
    set_clip_trigger_quantization,
    trigger_record,
    tap_tempo,
    get_selected_track,
    set_selected_track,
    get_selected_scene,
    set_selected_scene,
    get_scene_properties,
    set_scene_tempo,
    set_scene_time_signature,
    get_application_info,
    get_record_mode,
    set_record_mode,
    capture_and_insert_scene,
    create_locator,
    delete_locator,
    get_view_state,
    set_follow_song,
    set_draw_mode,
    select_clip_in_detail,
    get_punch_state,
    set_punch_in,
    set_punch_out,
    re_enable_automation,
    get_session_automation_record,
    set_session_automation_record,
    show_message,
    get_session_metadata,
    get_song_smpte_time,
    get_scene_info,
    get_scene_clips,
]
