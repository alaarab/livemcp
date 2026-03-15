"""Session-level tools: tempo, transport, time signature."""

import json
from typing import Any, Optional

from typing_extensions import TypedDict

from .. import __version__
from ..connection import get_connection, probe_command
from ..installer import get_install_status
from ..protocol import TRANSPORT_PROTOCOL_VERSION


class SessionInfo(TypedDict, total=False):
    tempo: float
    time_signature_numerator: int
    time_signature_denominator: int
    track_count: int
    return_track_count: int
    master_volume: float
    master_pan: float
    is_playing: bool
    loop: bool
    loop_start: float
    loop_length: float


class SongTimeInfo(TypedDict):
    current_song_time: float
    can_undo: bool
    can_redo: bool


class SelectedTrackInfo(TypedDict, total=False):
    index: int
    name: str
    type: str
    mute: bool
    solo: bool
    arm: bool
    color: int


class SelectedSceneInfo(TypedDict, total=False):
    index: int
    name: str
    color: int


class ApplicationInfo(TypedDict):
    major_version: int
    minor_version: int
    bugfix_version: int


class LiveMCPInfo(TypedDict, total=False):
    protocol_version: int
    supports_request_ids: bool
    transport: str
    legacy_compatibility_mode: bool
    namespaces: list[str]
    max_bridge: dict[str, Any]


class InstallStatusInfo(TypedDict, total=False):
    installed: bool
    needs_install: bool
    install_mode: str
    in_sync: bool
    installed_path: str
    source_path: str
    versioned_paths: list[dict[str, Any]]


class LiveMCPStatus(TypedDict, total=False):
    package_version: str
    client_protocol_version: int
    install_status: InstallStatusInfo
    remote_reachable: bool
    remote_info: Optional[LiveMCPInfo]
    max_bridge: Optional[dict[str, Any]]
    cached_server_info: Optional[LiveMCPInfo]
    remote_error: Optional[str]
    warnings: list[str]


class ApplicationDialogInfo(TypedDict, total=False):
    open_dialog_count: int
    current_dialog_message: str
    current_dialog_button_count: int


class MainViewsInfo(TypedDict):
    view_names: list[str]


class ViewVisibilityInfo(TypedDict):
    view_name: str
    visible: bool


class ViewStateInfo(TypedDict, total=False):
    selected_track: Optional[dict[str, Any]]
    detail_clip: Optional[dict[str, Any]]
    draw_mode: bool
    follow_song: bool
    browse_mode: Optional[bool]
    visible_views: list[str]


class SelectedDeviceState(TypedDict, total=False):
    track_scope: str
    track_index: Optional[int]
    track_name: Optional[str]
    device_index: Optional[int]
    device_name: Optional[str]
    class_name: Optional[str]
    type: Optional[int]
    is_active: Optional[bool]


class SelectedDeviceInfo(TypedDict, total=False):
    selected_device: Optional[SelectedDeviceState]
    track: dict[str, Any]


class SelectedParameterState(TypedDict, total=False):
    name: str
    value: float
    min: float
    max: float
    is_quantized: bool
    display_value: str
    track_scope: str
    track_index: Optional[int]
    track_name: Optional[str]
    device_index: Optional[int]
    device_name: Optional[str]
    class_name: Optional[str]
    type: Optional[int]
    is_active: Optional[bool]
    parameter_index: Optional[int]


class SelectedParameterInfo(TypedDict):
    selected_parameter: Optional[SelectedParameterState]


class SelectedChainState(TypedDict, total=False):
    name: str
    mute: bool
    solo: bool
    color_index: Optional[int]
    device_count: int
    volume: float
    track_scope: str
    track_index: Optional[int]
    track_name: Optional[str]
    device_index: Optional[int]
    device_name: Optional[str]
    class_name: Optional[str]
    type: Optional[int]
    is_active: Optional[bool]
    chain_index: Optional[int]


class SelectedChainInfo(TypedDict):
    selected_chain: Optional[SelectedChainState]


class SessionMetadataInfo(TypedDict, total=False):
    current_song_time: float
    song_length: float
    is_modified: bool
    current_cpu_load: float


class SongSmpteTimeInfo(TypedDict):
    hours: int
    minutes: int
    seconds: int
    frames: int


class SceneInfo(TypedDict, total=False):
    index: int
    name: str
    color: int
    tempo: float
    time_signature_numerator: int
    time_signature_denominator: int
    is_empty: bool
    clip_count: int


def _legacy_remote_info() -> LiveMCPInfo:
    return {
        "protocol_version": 1,
        "supports_request_ids": False,
        "transport": "tcp-json-lines",
        "legacy_compatibility_mode": True,
        "namespaces": ["live"],
        "max_bridge": _default_max_bridge_info(),
    }


def _default_max_bridge_info() -> dict[str, Any]:
    return {
        "reachable": False,
        "transport": "tcp-json-lines",
        "host": "127.0.0.1",
        "port": 9881,
        "capabilities": {
            "selected_device": False,
            "patcher_read": False,
            "patcher_write": False,
            "window_control": False,
            "save": False,
        },
    }


def get_session_info() -> SessionInfo:
    """Get the current Ableton Live session state.

    Returns tempo, time signature, track count, return track count,
    master track info, playback state, and loop settings.
    """
    result = get_connection().send_command("get_session_info", {})
    return result


def get_song_time() -> SongTimeInfo:
    """Get the current song time position and undo/redo availability.

    Returns current_song_time (in beats), can_undo, and can_redo.
    """
    result = get_connection().send_command("get_song_time", {})
    return result


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


def get_selected_track() -> SelectedTrackInfo:
    """Get information about the currently selected track.

    Returns the index, name, type, mute/solo/arm state, and color of the selected track.
    """
    result = get_connection().send_command("get_selected_track", {})
    return result


def set_selected_track(track_index: int) -> str:
    """Set the selected track in Ableton Live.

    Args:
        track_index: Zero-based index of the track to select.
    """
    result = get_connection().send_command("set_selected_track", {"track_index": track_index})
    return json.dumps(result)


def get_selected_scene() -> SelectedSceneInfo:
    """Get information about the currently selected scene.

    Returns the index, name, and color of the selected scene.
    """
    result = get_connection().send_command("get_selected_scene", {})
    return result


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


def get_application_info() -> ApplicationInfo:
    """Get Ableton Live application version info.

    Returns major_version, minor_version, and bugfix_version.
    """
    result = get_connection().send_command("get_application_info", {})
    return result


def get_livemcp_info() -> LiveMCPInfo:
    """Get LiveMCP remote-script transport capability information."""
    result = get_connection().send_command("get_livemcp_info", {})
    return result


def get_livemcp_status() -> LiveMCPStatus:
    """Get local install state and remote-script capability status.

    Returns package version, client transport version, local install status,
    remote-script capability info when reachable, and actionable warnings.
    """
    status = {
        "package_version": __version__,
        "client_protocol_version": TRANSPORT_PROTOCOL_VERSION,
        "install_status": get_install_status(),
        "remote_reachable": False,
        "remote_info": None,
        "max_bridge": None,
        "cached_server_info": get_connection().get_server_info(),
        "remote_error": None,
        "warnings": [],
    }

    try:
        status["remote_info"] = probe_command("get_livemcp_info", {}, timeout=2.0)
        status["remote_reachable"] = True
    except RuntimeError as exc:
        error_message = str(exc)
        if "Unknown command: get_livemcp_info" in error_message:
            status["remote_info"] = _legacy_remote_info()
            status["remote_reachable"] = True
        else:
            status["remote_error"] = error_message
    except Exception as exc:
        status["remote_error"] = str(exc)

    install_status = status["install_status"]
    if not install_status.get("installed"):
        status["warnings"].append("LiveMCP remote script is not installed in Ableton.")
    elif install_status.get("needs_install"):
        status["warnings"].append(
            "Installed LiveMCP remote script is out of sync with the current source; run --install."
        )

    remote_info = status["remote_info"]
    status["max_bridge"] = (
        remote_info.get("max_bridge", _default_max_bridge_info()) if remote_info else None
    )
    if not status["remote_reachable"]:
        status["warnings"].append("LiveMCP socket is not currently reachable.")
    elif remote_info and remote_info.get("protocol_version", 0) < TRANSPORT_PROTOCOL_VERSION:
        status["warnings"].append(
            "Ableton is running an older LiveMCP transport protocol; reinstall and restart Ableton."
        )

    if status["remote_reachable"] and remote_info:
        namespaces = remote_info.get("namespaces", [])
        if "max" not in namespaces:
            status["warnings"].append(
                "The running LiveMCP remote script does not advertise Max for Live support."
            )
        elif status["max_bridge"] and not status["max_bridge"].get("reachable"):
            status["warnings"].append(
                "Max bridge is not currently reachable; Max for Live patcher tools will fail until a local bridge session is available."
            )

    return status


def get_application_dialog() -> ApplicationDialogInfo:
    """Get information about the current Ableton dialog box.

    Returns open dialog count, current dialog message, and current dialog button count.
    """
    result = get_connection().send_command("get_application_dialog", {})
    return result


def press_current_dialog_button(index: int) -> str:
    """Press a button in the current Ableton dialog box.

    Args:
        index: Zero-based button index in the current dialog.
    """
    result = get_connection().send_command("press_current_dialog_button", {"index": index})
    return json.dumps(result)


def get_application_cpu_usage() -> str:
    """Get Ableton application's average and peak CPU usage."""
    result = get_connection().send_command("get_application_cpu_usage", {})
    return json.dumps(result)


def get_available_main_views() -> MainViewsInfo:
    """Get the canonical Ableton view names accepted by view control tools."""
    result = get_connection().send_command("get_available_main_views", {})
    return result


def is_view_visible(view_name: str) -> ViewVisibilityInfo:
    """Get whether an Ableton view is currently visible.

    Args:
        view_name: View name such as 'Browser', 'Arranger', 'Session',
                   'Detail', 'Detail/Clip', or 'Detail/DeviceChain'.
    """
    result = get_connection().send_command("is_view_visible", {"view_name": view_name})
    return result


def show_view(view_name: str) -> str:
    """Show an Ableton UI view.

    Args:
        view_name: View name such as 'Browser', 'Arranger', 'Session',
                   'Detail', 'Detail/Clip', or 'Detail/DeviceChain'.
    """
    result = get_connection().send_command("show_view", {"view_name": view_name})
    return json.dumps(result)


def hide_view(view_name: str) -> str:
    """Hide an Ableton UI view.

    Args:
        view_name: View name such as 'Browser', 'Arranger', 'Session',
                   'Detail', 'Detail/Clip', or 'Detail/DeviceChain'.
    """
    result = get_connection().send_command("hide_view", {"view_name": view_name})
    return json.dumps(result)


def focus_view(view_name: str) -> str:
    """Show and focus an Ableton UI view.

    Args:
        view_name: View name such as 'Browser', 'Arranger', 'Session',
                   'Detail', 'Detail/Clip', or 'Detail/DeviceChain'.
    """
    result = get_connection().send_command("focus_view", {"view_name": view_name})
    return json.dumps(result)


def toggle_browse() -> str:
    """Toggle Ableton's browser hot-swap mode for the selected device."""
    result = get_connection().send_command("toggle_browse", {})
    return json.dumps(result)


def get_record_mode() -> str:
    """Get whether arrangement recording is armed.

    Returns record_mode (True if armed, False otherwise).
    """
    result = get_connection().send_command("get_record_mode", {})
    return json.dumps(result)


def get_link_state() -> str:
    """Get Ableton Link and Tempo Follower state."""
    result = get_connection().send_command("get_link_state", {})
    return json.dumps(result)


def set_ableton_link_enabled(enabled: bool) -> str:
    """Enable or disable Ableton Link.

    Args:
        enabled: True to enable Link, False to disable it.
    """
    result = get_connection().send_command("set_ableton_link_enabled", {"enabled": enabled})
    return json.dumps(result)


def set_ableton_link_start_stop_sync_enabled(enabled: bool) -> str:
    """Enable or disable Ableton Link Start/Stop Sync.

    Args:
        enabled: True to enable Start/Stop Sync, False to disable it.
    """
    result = get_connection().send_command(
        "set_ableton_link_start_stop_sync_enabled",
        {"enabled": enabled},
    )
    return json.dumps(result)


def set_tempo_follower_enabled(enabled: bool) -> str:
    """Enable or disable Tempo Follower.

    Args:
        enabled: True to enable Tempo Follower, False to disable it.
    """
    result = get_connection().send_command("set_tempo_follower_enabled", {"enabled": enabled})
    return json.dumps(result)


def get_count_in_state() -> str:
    """Get metronome count-in settings and current counting-in state."""
    result = get_connection().send_command("get_count_in_state", {})
    return json.dumps(result)


def get_session_record_status() -> str:
    """Get Session Record state and current record status."""
    result = get_connection().send_command("get_session_record_status", {})
    return json.dumps(result)


def set_session_record(enabled: bool) -> str:
    """Enable or disable Session Record.

    Args:
        enabled: True to enable Session Record, False to disable it.
    """
    result = get_connection().send_command("set_session_record", {"enabled": enabled})
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


def get_view_state() -> ViewStateInfo:
    """Get the current view state in Ableton Live.

    Returns the selected track, detail clip (if any), draw mode, and follow song state.
    """
    result = get_connection().send_command("get_view_state", {})
    return result


def get_selected_device() -> SelectedDeviceInfo:
    """Get the currently selected device on the selected track."""
    result = get_connection().send_command("get_selected_device", {})
    return result


def select_device(track_index: int, device_index: int) -> str:
    """Select a device on a track in Ableton's UI.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the device in the track's device chain.
    """
    result = get_connection().send_command("select_device", {
        "track_index": track_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def get_selected_parameter() -> SelectedParameterInfo:
    """Get the currently selected Ableton device parameter."""
    result = get_connection().send_command("get_selected_parameter", {})
    return result


def get_selected_chain() -> SelectedChainInfo:
    """Get the currently selected rack chain in Ableton's UI."""
    result = get_connection().send_command("get_selected_chain", {})
    return result


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


def get_session_metadata() -> SessionMetadataInfo:
    """Get session metadata: modified state, current song time, song length, and CPU load.

    Returns is_modified, current_song_time (beats), song_length (beats),
    and current_cpu_load (if available).
    """
    result = get_connection().send_command("get_session_metadata", {})
    return result


def get_song_smpte_time() -> SongSmpteTimeInfo:
    """Get the current song time in SMPTE (timecode) format.

    Returns hours, minutes, seconds, and frames.
    """
    result = get_connection().send_command("get_song_smpte_time", {})
    return result


def get_scene_info(scene_index: int) -> SceneInfo:
    """Get detailed information about a specific scene.

    Returns the scene name, color, tempo (if tempo_enabled), time signature
    (if available), is_empty flag (if available), and clip_count across all tracks.

    Args:
        scene_index: Zero-based index of the scene.
    """
    result = get_connection().send_command("get_scene_info", {"scene_index": scene_index})
    return result


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
    get_livemcp_info,
    get_livemcp_status,
    get_application_dialog,
    press_current_dialog_button,
    get_application_cpu_usage,
    get_available_main_views,
    is_view_visible,
    show_view,
    hide_view,
    focus_view,
    toggle_browse,
    get_record_mode,
    get_link_state,
    set_ableton_link_enabled,
    set_ableton_link_start_stop_sync_enabled,
    set_tempo_follower_enabled,
    get_count_in_state,
    get_session_record_status,
    set_session_record,
    set_record_mode,
    capture_and_insert_scene,
    create_locator,
    delete_locator,
    get_view_state,
    get_selected_device,
    select_device,
    get_selected_parameter,
    get_selected_chain,
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
