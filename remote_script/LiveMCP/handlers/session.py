"""Session-level handlers: tempo, transport, time signature."""

from ..protocol import TRANSPORT_PROTOCOL_VERSION

DEFAULT_MAIN_VIEWS = [
    "Browser",
    "Arranger",
    "Session",
    "Detail",
    "Detail/Clip",
    "Detail/DeviceChain",
]

VIEW_NAME_ALIASES = {
    "browser": "Browser",
    "arranger": "Arranger",
    "arrangement": "Arranger",
    "session": "Session",
    "detail": "Detail",
    "clip": "Detail/Clip",
    "detailclip": "Detail/Clip",
    "device": "Detail/DeviceChain",
    "devicechain": "Detail/DeviceChain",
    "detaildevicechain": "Detail/DeviceChain",
}


def _normalize_view_name(view_name):
    if view_name is None:
        raise ValueError("Missing required parameter: view_name")
    raw = str(view_name).strip()
    if not raw:
        raise ValueError("view_name cannot be empty")
    normalized = raw.lower().replace(" ", "").replace("_", "").replace("-", "").replace("/", "")
    canonical = VIEW_NAME_ALIASES.get(normalized)
    if canonical is None:
        raise ValueError(
            "Unsupported view_name '{}'. Supported values: {}".format(
                raw, ", ".join(DEFAULT_MAIN_VIEWS)
            )
        )
    return canonical


def _get_application_view(control_surface):
    return control_surface.application().view


def _get_available_main_views(app_view):
    try:
        return list(app_view.available_main_views())
    except TypeError:
        return list(app_view.available_main_views)
    except Exception:
        return list(DEFAULT_MAIN_VIEWS)


def _describe_track_location(song, track):
    if track is None:
        return {"scope": None, "index": None, "name": None}
    try:
        return {
            "scope": "track",
            "index": list(song.tracks).index(track),
            "name": track.name,
        }
    except ValueError:
        pass
    try:
        return {
            "scope": "return",
            "index": list(song.return_tracks).index(track),
            "name": track.name,
        }
    except ValueError:
        pass
    if track == song.master_track:
        return {"scope": "master", "index": None, "name": track.name}
    return {"scope": "unknown", "index": None, "name": getattr(track, "name", None)}


def _get_selected_device_on_track(track):
    try:
        return track.view.selected_device
    except Exception:
        return None


def _describe_device(song, track, device):
    track_info = _describe_track_location(song, track)
    device_index = None
    try:
        device_index = list(track.devices).index(device)
    except Exception:
        pass
    return {
        "track_scope": track_info["scope"],
        "track_index": track_info["index"],
        "track_name": track_info["name"],
        "device_index": device_index,
        "device_name": getattr(device, "name", None),
        "class_name": getattr(device, "class_name", None),
        "type": int(device.type) if hasattr(device, "type") else None,
        "is_active": getattr(device, "is_active", None),
    }


def get_session_info(control_surface, params):
    """Return global session state."""
    song = control_surface.song()
    master = song.master_track
    return {
        "tempo": song.tempo,
        "time_signature_numerator": song.signature_numerator,
        "time_signature_denominator": song.signature_denominator,
        "track_count": len(song.tracks),
        "return_track_count": len(song.return_tracks),
        "master_volume": master.mixer_device.volume.value,
        "master_pan": master.mixer_device.panning.value,
        "is_playing": song.is_playing,
        "loop": song.loop,
        "loop_start": song.loop_start,
        "loop_length": song.loop_length,
    }


def get_livemcp_info(control_surface, params):
    """Return transport capability information for the installed remote script."""
    server = getattr(control_surface, "_server", None)
    max_bridge = (
        server.get_max_bridge_info()
        if server is not None
        else {
            "reachable": False,
            "capabilities": {
                "selected_device": False,
                "patcher_read": False,
                "patcher_write": False,
                "window_control": False,
                "save": False,
            },
            "error_code": "max/bridge-unavailable",
            "error_message": "LiveMCP Max bridge is not initialized.",
        }
    )
    return {
        "protocol_version": TRANSPORT_PROTOCOL_VERSION,
        "supports_request_ids": True,
        "transport": "tcp-json-lines",
        "namespaces": ["live", "docs", "max"],
        "max_bridge": max_bridge,
    }


def get_song_time(control_surface, params):
    """Return current song time and undo/redo state."""
    song = control_surface.song()
    return {
        "current_song_time": song.current_song_time,
        "can_undo": song.can_undo,
        "can_redo": song.can_redo,
    }


def get_cue_points(control_surface, params):
    """Return list of cue points."""
    song = control_surface.song()
    cue_points = []
    for i, cp in enumerate(song.cue_points):
        cue_points.append({
            "index": i,
            "name": cp.name,
            "time": cp.time,
        })
    return {"cue_points": cue_points}


def set_tempo(control_surface, params):
    """Set the session tempo in BPM."""
    tempo = params.get("tempo")
    if tempo is None:
        raise ValueError("Missing required parameter: tempo")
    tempo = float(tempo)
    if tempo < 20 or tempo > 999:
        raise ValueError("Tempo must be between 20 and 999 BPM")
    control_surface.song().tempo = tempo
    return {"tempo": tempo}


def start_playback(control_surface, params):
    """Start transport playback."""
    control_surface.song().start_playing()
    return {"is_playing": True}


def stop_playback(control_surface, params):
    """Stop transport playback."""
    control_surface.song().stop_playing()
    return {"is_playing": False}


def undo(control_surface, params):
    """Undo the last action."""
    control_surface.song().undo()
    return {"undone": True}


def redo(control_surface, params):
    """Redo the last undone action."""
    control_surface.song().redo()
    return {"redone": True}


def set_time_signature(control_surface, params):
    """Set the song time signature."""
    numerator = params.get("numerator")
    denominator = params.get("denominator")
    if numerator is None or denominator is None:
        raise ValueError("Missing required parameters: numerator and denominator")
    song = control_surface.song()
    song.signature_numerator = int(numerator)
    song.signature_denominator = int(denominator)
    return {
        "signature_numerator": song.signature_numerator,
        "signature_denominator": song.signature_denominator,
    }


def set_loop_region(control_surface, params):
    """Set loop on/off, start, and/or length."""
    song = control_surface.song()
    loop_on = params.get("loop_on")
    loop_start = params.get("loop_start")
    loop_length = params.get("loop_length")
    if loop_on is not None:
        song.loop = bool(loop_on)
    if loop_start is not None:
        song.loop_start = float(loop_start)
    if loop_length is not None:
        song.loop_length = float(loop_length)
    return {
        "loop": song.loop,
        "loop_start": song.loop_start,
        "loop_length": song.loop_length,
    }


def set_song_time(control_surface, params):
    """Set the current song time (playhead position)."""
    time = params.get("time")
    if time is None:
        raise ValueError("Missing required parameter: time")
    song = control_surface.song()
    song.current_song_time = float(time)
    return {"current_song_time": song.current_song_time}


def continue_playing(control_surface, params):
    """Continue playback from current position."""
    control_surface.song().continue_playing()
    return {"continued": True}


def stop_all_clips(control_surface, params):
    """Stop all playing clips."""
    control_surface.song().stop_all_clips()
    return {"stopped": True}


def capture_midi(control_surface, params):
    """Capture recently played MIDI."""
    control_surface.song().capture_midi()
    return {"captured": True}


def set_metronome(control_surface, params):
    """Enable or disable the metronome."""
    on = params.get("on")
    if on is None:
        raise ValueError("Missing required parameter: on")
    control_surface.song().metronome = bool(on)
    return {"metronome": control_surface.song().metronome}


def set_groove_amount(control_surface, params):
    """Set the global groove amount."""
    amount = params.get("amount")
    if amount is None:
        raise ValueError("Missing required parameter: amount")
    control_surface.song().groove_amount = float(amount)
    return {"groove_amount": control_surface.song().groove_amount}


def set_scale(control_surface, params):
    """Set the song root note and/or scale name (Live 12+)."""
    song = control_surface.song()
    root_note = params.get("root_note")
    scale_name = params.get("scale_name")
    try:
        if root_note is not None:
            song.root_note = int(root_note)
        if scale_name is not None:
            song.scale_name = str(scale_name)
        result = {}
        try:
            result["root_note"] = song.root_note
        except Exception:
            pass
        try:
            result["scale_name"] = song.scale_name
        except Exception:
            pass
        return result
    except Exception as e:
        raise ValueError("set_scale requires Live 12 or later: {}".format(str(e)))


def jump_to_next_cue(control_surface, params):
    """Jump to the next cue point."""
    control_surface.song().jump_to_next_cue()
    return {"jumped": "next"}


def jump_to_prev_cue(control_surface, params):
    """Jump to the previous cue point."""
    control_surface.song().jump_to_prev_cue()
    return {"jumped": "prev"}


def jump_to_cue(control_surface, params):
    """Jump to a specific cue point by index."""
    index = params.get("index")
    if index is None:
        raise ValueError("Missing required parameter: index")
    index = int(index)
    song = control_surface.song()
    cue_points = song.cue_points
    if index < 0 or index >= len(cue_points):
        raise ValueError("Cue point index {} out of range (0-{})".format(index, len(cue_points) - 1))
    cue_points[index].jump()
    return {"jumped_to": index, "name": cue_points[index].name}


def set_midi_recording_quantization(control_surface, params):
    """Set the MIDI recording quantization value."""
    value = params.get("value")
    if value is None:
        raise ValueError("Missing required parameter: value")
    control_surface.song().midi_recording_quantization = int(value)
    return {"midi_recording_quantization": int(value)}


def set_clip_trigger_quantization(control_surface, params):
    """Set the clip trigger quantization value."""
    value = params.get("value")
    if value is None:
        raise ValueError("Missing required parameter: value")
    control_surface.song().clip_trigger_quantization = int(value)
    return {"clip_trigger_quantization": int(value)}


def trigger_record(control_surface, params):
    """Trigger session record."""
    control_surface.song().trigger_session_record()
    return {"recording": True}


def tap_tempo(control_surface, params):
    """Tap tempo."""
    control_surface.song().tap_tempo()
    return {"tapped": True}


def get_selected_track(control_surface, params):
    """Return info about the currently selected track."""
    song = control_surface.song()
    track = song.view.selected_track
    if track is None:
        return {"selected_track": None}
    tracks = list(song.tracks)
    try:
        index = tracks.index(track)
        track_type = "midi" if track.has_midi_input else ("audio" if track.has_audio_input else "unknown")
        return {
            "index": index,
            "name": track.name,
            "type": track_type,
            "mute": track.mute,
            "solo": track.solo,
            "arm": track.arm,
            "color_index": track.color_index,
        }
    except ValueError:
        return {"selected_track": "master_or_return"}


def set_selected_track(control_surface, params):
    """Set the selected track by index."""
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)
    song = control_surface.song()
    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))
    song.view.selected_track = song.tracks[track_index]
    return {"selected_track_index": track_index}


def get_selected_scene(control_surface, params):
    """Return info about the currently selected scene."""
    song = control_surface.song()
    scene = song.view.selected_scene
    if scene is None:
        return {"selected_scene": None}
    scenes = list(song.scenes)
    try:
        index = scenes.index(scene)
        return {
            "index": index,
            "name": scene.name,
            "color_index": scene.color_index,
        }
    except ValueError:
        return {"selected_scene": None}


def set_selected_scene(control_surface, params):
    """Set the selected scene by index."""
    scene_index = params.get("scene_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    scene_index = int(scene_index)
    song = control_surface.song()
    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))
    song.view.selected_scene = song.scenes[scene_index]
    return {"selected_scene_index": scene_index}


def get_scene_properties(control_surface, params):
    """Get properties of a specific scene."""
    song = control_surface.song()
    scene_index = params.get("scene_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    scene_index = int(scene_index)
    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range".format(scene_index))
    scene = song.scenes[scene_index]
    result = {
        "index": scene_index,
        "name": scene.name,
        "tempo": scene.tempo,  # -1.0 means no scene tempo set
        "color": scene.color,
        "color_index": scene.color_index,
    }
    try:
        result["tempo_enabled"] = scene.tempo_enabled
        result["time_signature_numerator"] = scene.time_signature_numerator
        result["time_signature_denominator"] = scene.time_signature_denominator
        result["time_signature_enabled"] = scene.time_signature_enabled
    except AttributeError:
        pass  # Live 12-only properties
    return result


def set_scene_tempo(control_surface, params):
    """Set the tempo for a scene. Use 0 to clear scene tempo."""
    song = control_surface.song()
    scene_index = params.get("scene_index")
    tempo = params.get("tempo")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    if tempo is None:
        raise ValueError("Missing required parameter: tempo")
    scene_index = int(scene_index)
    tempo = float(tempo)
    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))
    scene = song.scenes[scene_index]
    if tempo <= 0:
        try:
            scene.tempo_enabled = False
        except AttributeError:
            scene.tempo = 120.0  # fallback: can't clear on older Live
    else:
        scene.tempo = tempo
        try:
            scene.tempo_enabled = True
        except AttributeError:
            pass
    return {"scene_index": scene_index, "tempo": scene.tempo}


def set_scene_time_signature(control_surface, params):
    """Set time signature for a scene (Live 12+)."""
    song = control_surface.song()
    scene_index = params.get("scene_index")
    numerator = params.get("numerator")
    denominator = params.get("denominator")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    if numerator is None:
        raise ValueError("Missing required parameter: numerator")
    if denominator is None:
        raise ValueError("Missing required parameter: denominator")
    scene_index = int(scene_index)
    numerator = int(numerator)
    denominator = int(denominator)
    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))
    scene = song.scenes[scene_index]
    scene.time_signature_numerator = numerator
    scene.time_signature_denominator = denominator
    return {"scene_index": scene_index, "numerator": numerator, "denominator": denominator}


def get_application_info(control_surface, params):
    """Return Ableton Live version info."""
    app = control_surface.application()
    return {
        "major_version": app.get_major_version(),
        "minor_version": app.get_minor_version(),
        "bugfix_version": app.get_bugfix_version(),
    }


def get_application_dialog(control_surface, params):
    """Return the current Ableton dialog state."""
    app = control_surface.application()
    return {
        "open_dialog_count": app.open_dialog_count,
        "current_dialog_message": app.current_dialog_message,
        "current_dialog_button_count": app.current_dialog_button_count,
    }


def press_current_dialog_button(control_surface, params):
    """Press a button in the current Ableton dialog box."""
    index = params.get("index")
    if index is None:
        raise ValueError("Missing required parameter: index")
    index = int(index)

    app = control_surface.application()
    button_count = app.current_dialog_button_count
    if app.open_dialog_count <= 0 or button_count <= 0:
        raise ValueError("No dialog is currently open")
    if index < 0 or index >= button_count:
        raise ValueError("Dialog button index {} out of range (0-{})".format(index, button_count - 1))

    app.press_current_dialog_button(index)
    return {
        "pressed_index": index,
        "open_dialog_count": app.open_dialog_count,
        "current_dialog_message": app.current_dialog_message,
        "current_dialog_button_count": app.current_dialog_button_count,
    }


def get_application_cpu_usage(control_surface, params):
    """Return Ableton application's average and peak CPU usage."""
    app = control_surface.application()
    return {
        "average_process_usage": app.average_process_usage,
        "peak_process_usage": app.peak_process_usage,
    }


def get_available_main_views(control_surface, params):
    """Return the canonical view names available for Application.View helpers."""
    app_view = _get_application_view(control_surface)
    return {"available_main_views": _get_available_main_views(app_view)}


def is_view_visible(control_surface, params):
    """Return whether a given Ableton view is currently visible."""
    app_view = _get_application_view(control_surface)
    view_name = _normalize_view_name(params.get("view_name"))
    return {
        "view_name": view_name,
        "visible": bool(app_view.is_view_visible(view_name)),
    }


def show_view(control_surface, params):
    """Show a given Ableton view."""
    app_view = _get_application_view(control_surface)
    view_name = _normalize_view_name(params.get("view_name"))
    app_view.show_view(view_name)
    return {"view_name": view_name, "visible": bool(app_view.is_view_visible(view_name))}


def hide_view(control_surface, params):
    """Hide a given Ableton view."""
    app_view = _get_application_view(control_surface)
    view_name = _normalize_view_name(params.get("view_name"))
    app_view.hide_view(view_name)
    return {"view_name": view_name, "visible": bool(app_view.is_view_visible(view_name))}


def focus_view(control_surface, params):
    """Focus a given Ableton view."""
    app_view = _get_application_view(control_surface)
    view_name = _normalize_view_name(params.get("view_name"))
    app_view.focus_view(view_name)
    return {"view_name": view_name, "visible": bool(app_view.is_view_visible(view_name))}


def toggle_browse(control_surface, params):
    """Toggle Ableton's browse mode."""
    app_view = _get_application_view(control_surface)
    app_view.toggle_browse()
    result = {}
    try:
        result["browse_mode"] = bool(app_view.browse_mode)
    except Exception:
        result["browse_mode"] = None
    return result


def get_record_mode(control_surface, params):
    """Return whether arrangement recording is armed."""
    song = control_surface.song()
    return {"record_mode": song.record_mode}


def get_link_state(control_surface, params):
    """Return Ableton Link, Start/Stop Sync, and Tempo Follower state."""
    song = control_surface.song()
    result = {}
    property_map = {
        "is_ableton_link_enabled": "ableton_link_enabled",
        "is_ableton_link_start_stop_sync_enabled": "ableton_link_start_stop_sync_enabled",
        "tempo_follower_enabled": "tempo_follower_enabled",
    }
    for source_name, target_name in property_map.items():
        try:
            result[target_name] = bool(getattr(song, source_name))
        except Exception:
            result[target_name] = None
    return result


def set_ableton_link_enabled(control_surface, params):
    """Enable or disable Ableton Link."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    song = control_surface.song()
    song.is_ableton_link_enabled = bool(enabled)
    return {"ableton_link_enabled": bool(song.is_ableton_link_enabled)}


def set_ableton_link_start_stop_sync_enabled(control_surface, params):
    """Enable or disable Ableton Link Start/Stop Sync."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    song = control_surface.song()
    song.is_ableton_link_start_stop_sync_enabled = bool(enabled)
    return {
        "ableton_link_start_stop_sync_enabled": bool(
            song.is_ableton_link_start_stop_sync_enabled
        )
    }


def set_tempo_follower_enabled(control_surface, params):
    """Enable or disable Tempo Follower."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    song = control_surface.song()
    song.tempo_follower_enabled = bool(enabled)
    return {"tempo_follower_enabled": bool(song.tempo_follower_enabled)}


def get_count_in_state(control_surface, params):
    """Return count-in duration and active counting-in state."""
    song = control_surface.song()
    return {
        "count_in_duration": int(song.count_in_duration),
        "is_counting_in": bool(song.is_counting_in),
    }


def get_session_record_status(control_surface, params):
    """Return Session Record state and status value."""
    song = control_surface.song()
    result = {"session_record": bool(song.session_record)}
    try:
        result["session_record_status"] = int(song.session_record_status)
    except Exception:
        result["session_record_status"] = None
    return result


def set_session_record(control_surface, params):
    """Enable or disable Session Record."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    song = control_surface.song()
    song.session_record = bool(enabled)
    result = {"session_record": bool(song.session_record)}
    try:
        result["session_record_status"] = int(song.session_record_status)
    except Exception:
        result["session_record_status"] = None
    return result


def set_record_mode(control_surface, params):
    """Enable or disable arrangement recording."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    song = control_surface.song()
    song.record_mode = bool(enabled)
    return {"record_mode": song.record_mode}


def capture_and_insert_scene(control_surface, params):
    """Capture currently playing clips into a new scene."""
    song = control_surface.song()
    song.capture_and_insert_scene()
    return {"captured": True, "scene_count": len(song.scenes)}


def create_locator(control_surface, params):
    """Create a cue point (locator) at the current playhead position.

    IMPORTANT: Ableton's set_or_delete_cue() operates at the playhead position
    from the *previous* tick. You MUST call set_song_time first to position the
    playhead, then call create_locator in a separate command.
    """
    song = control_surface.song()
    before_count = len(song.cue_points)
    song.set_or_delete_cue()
    after_count = len(song.cue_points)
    created = after_count > before_count

    if not created:
        # Toggle deleted an existing cue at this position; call again to re-create
        song.set_or_delete_cue()
        after_count = len(song.cue_points)
        created = after_count > before_count

    return {"created": created, "playhead_time": song.current_song_time}


def delete_locator(control_surface, params):
    """Delete a cue point (locator) by index.

    IMPORTANT: Ableton's set_or_delete_cue() operates at the playhead position
    from the *previous* tick. This handler moves the playhead to the cue point's
    time; a second call will then toggle at that position. For reliable deletion,
    call set_song_time to the cue's time first, then call delete_locator.
    """
    song = control_surface.song()
    cue_index = params.get("index")
    if cue_index is None:
        raise ValueError("Missing required parameter: index")
    cue_index = int(cue_index)
    cue_points = list(song.cue_points)
    if cue_index < 0 or cue_index >= len(cue_points):
        raise ValueError("Cue index {} out of range (0-{})".format(cue_index, len(cue_points) - 1))

    cue = cue_points[cue_index]
    target_time = cue.time

    # Move playhead to the cue's time for the *next* toggle call
    song.current_song_time = target_time

    # Toggle — this operates at the *previous* playhead position, not target_time
    before_count = len(cue_points)
    song.set_or_delete_cue()
    after_count = len(song.cue_points)

    # Check if the intended cue was actually deleted
    still_exists = any(abs(cp.time - target_time) < 0.001 for cp in song.cue_points)
    if still_exists and after_count >= before_count:
        return {"deleted": False, "time": target_time,
                "message": "Playhead positioned at cue time. Call delete_locator again "
                           "to delete now that playhead is at the correct position."}

    return {"deleted": True, "time": target_time}


def get_view_state(control_surface, params):
    """Return current view state: selected track, detail clip, draw mode, follow song."""
    song = control_surface.song()
    view = song.view
    selected_track = view.selected_track
    tracks = list(song.tracks)
    track_info = None
    try:
        idx = tracks.index(selected_track)
        track_info = {"index": idx, "name": selected_track.name}
    except ValueError:
        track_info = {"index": None, "name": selected_track.name if selected_track else None}
    detail_clip = view.detail_clip
    clip_info = None
    if detail_clip is not None:
        clip_info = {"name": detail_clip.name, "length": detail_clip.length}
    result = {
        "selected_track": track_info,
        "detail_clip": clip_info,
        "draw_mode": view.draw_mode,
        "follow_song": view.follow_song,
    }
    app_view = _get_application_view(control_surface)
    try:
        result["browse_mode"] = app_view.browse_mode
    except Exception:
        pass
    try:
        result["visible_views"] = [
            view_name
            for view_name in _get_available_main_views(app_view)
            if app_view.is_view_visible(view_name)
        ]
    except Exception:
        pass
    return result


def get_selected_device(control_surface, params):
    """Return the selected device on the selected track."""
    song = control_surface.song()
    track = song.view.selected_track
    if track is None:
        return {"selected_device": None}
    device = _get_selected_device_on_track(track)
    if device is None:
        return {"selected_device": None, "track": _describe_track_location(song, track)}
    return {"selected_device": _describe_device(song, track, device)}


def select_device(control_surface, params):
    """Select a device on a track."""
    track_index = params.get("track_index")
    device_index = params.get("device_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if device_index is None:
        raise ValueError("Missing required parameter: device_index")
    track_index = int(track_index)
    device_index = int(device_index)

    song = control_surface.song()
    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))
    track = song.tracks[track_index]
    if device_index < 0 or device_index >= len(track.devices):
        raise ValueError("Device index {0} out of range (0-{1})".format(
            device_index, len(track.devices) - 1))

    device = track.devices[device_index]
    song.view.selected_track = track
    song.view.select_device(device)
    return {"selected_device": _describe_device(song, track, device)}


def get_selected_parameter(control_surface, params):
    """Return the currently selected parameter."""
    song = control_surface.song()
    parameter = song.view.selected_parameter
    if parameter is None:
        return {"selected_parameter": None}

    result = {
        "name": parameter.name,
        "value": parameter.value,
        "min": parameter.min,
        "max": parameter.max,
        "is_quantized": parameter.is_quantized,
        "display_value": str(parameter),
    }

    track = song.view.selected_track
    device = _get_selected_device_on_track(track) if track is not None else None
    if device is not None:
        result.update(_describe_device(song, track, device))
        try:
            result["parameter_index"] = list(device.parameters).index(parameter)
        except ValueError:
            result["parameter_index"] = None

    return {"selected_parameter": result}


def get_selected_chain(control_surface, params):
    """Return the currently selected chain."""
    song = control_surface.song()
    try:
        chain = song.view.selected_chain
    except Exception:
        return {"selected_chain": None}
    if chain is None:
        return {"selected_chain": None}

    result = {
        "name": chain.name,
        "mute": chain.mute,
        "solo": chain.solo,
        "color_index": getattr(chain, "color_index", None),
        "device_count": len(chain.devices),
        "volume": chain.mixer_device.volume.value,
    }

    track = song.view.selected_track
    device = _get_selected_device_on_track(track) if track is not None else None
    if device is not None and hasattr(device, "chains"):
        result.update(_describe_device(song, track, device))
        try:
            result["chain_index"] = list(device.chains).index(chain)
        except ValueError:
            result["chain_index"] = None

    return {"selected_chain": result}


def set_follow_song(control_surface, params):
    """Enable or disable follow song mode."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    control_surface.song().view.follow_song = bool(enabled)
    return {"follow_song": control_surface.song().view.follow_song}


def set_draw_mode(control_surface, params):
    """Enable or disable draw mode."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    control_surface.song().view.draw_mode = bool(enabled)
    return {"draw_mode": control_surface.song().view.draw_mode}


def select_clip_in_detail(control_surface, params):
    """Select a clip in the detail view."""
    track_index = params.get("track_index")
    clip_index = params.get("clip_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if clip_index is None:
        raise ValueError("Missing required parameter: clip_index")
    track_index = int(track_index)
    clip_index = int(clip_index)
    song = control_surface.song()
    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))
    track = song.tracks[track_index]
    if clip_index < 0 or clip_index >= len(track.clip_slots):
        raise ValueError("Clip index {0} out of range (0-{1})".format(
            clip_index, len(track.clip_slots) - 1))
    clip_slot = track.clip_slots[clip_index]
    if not clip_slot.has_clip:
        raise ValueError("No clip at track {0}, slot {1}".format(track_index, clip_index))
    song.view.detail_clip = clip_slot.clip
    return {"track_index": track_index, "clip_index": clip_index, "clip_name": clip_slot.clip.name}


def get_punch_state(control_surface, params):
    """Return punch in/out state."""
    song = control_surface.song()
    return {"punch_in": song.punch_in, "punch_out": song.punch_out}


def set_punch_in(control_surface, params):
    """Enable or disable punch in."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    value = bool(enabled)
    control_surface.song().punch_in = value
    return {"punch_in": value}


def set_punch_out(control_surface, params):
    """Enable or disable punch out."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    value = bool(enabled)
    control_surface.song().punch_out = value
    return {"punch_out": value}


def re_enable_automation(control_surface, params):
    """Re-enable automation that was overridden by manual changes."""
    control_surface.song().re_enable_automation()
    return {"re_enabled": True}


def get_session_automation_record(control_surface, params):
    """Return whether session automation recording is enabled."""
    song = control_surface.song()
    return {"session_automation_record": song.session_automation_record}


def set_session_automation_record(control_surface, params):
    """Enable or disable session automation recording."""
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    value = bool(enabled)
    control_surface.song().session_automation_record = value
    return {"session_automation_record": value}


def show_message(control_surface, params):
    """Display a message in the Ableton Live status bar."""
    message = params.get("message")
    if message is None:
        raise ValueError("Missing required parameter: message")
    msg = str(message)
    control_surface.show_message(msg)
    return {"shown": True, "message": msg}


def get_session_metadata(control_surface, params):
    """Return session metadata: modified state, song time, length, and CPU load."""
    song = control_surface.song()
    result = {
        "current_song_time": song.current_song_time,
        "song_length": song.song_length,
    }
    try:
        result["is_modified"] = song.is_modified
    except Exception:
        pass
    try:
        result["current_cpu_load"] = song.current_cpu_load
    except Exception:
        pass
    return result


def get_song_smpte_time(control_surface, params):
    """Return the current song time in SMPTE format."""
    song = control_surface.song()
    smpte = song.get_current_smpte_song_time(0)
    return {
        "hours": smpte.hours,
        "minutes": smpte.minutes,
        "seconds": smpte.seconds,
        "frames": smpte.frames,
    }


def get_scene_info(control_surface, params):
    """Return detailed info about a scene by index, including clip count."""
    song = control_surface.song()
    scene_index = params.get("scene_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    scene_index = int(scene_index)
    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))
    scene = song.scenes[scene_index]
    result = {
        "index": scene_index,
        "name": scene.name,
        "color": scene.color,
    }
    try:
        if scene.tempo_enabled:
            result["tempo"] = scene.tempo
    except AttributeError:
        pass
    try:
        result["time_signature_numerator"] = scene.time_signature_numerator
        result["time_signature_denominator"] = scene.time_signature_denominator
    except AttributeError:
        pass
    try:
        result["is_empty"] = scene.is_empty
    except Exception:
        pass
    # Count clips across all tracks for this scene
    clip_count = 0
    for track in song.tracks:
        if scene_index < len(track.clip_slots):
            if track.clip_slots[scene_index].has_clip:
                clip_count += 1
    result["clip_count"] = clip_count
    return result


def get_scene_clips(control_surface, params):
    """Get all clips in a scene across all tracks."""
    song = control_surface.song()
    scene_index = params.get("scene_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    scene_index = int(scene_index)
    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))

    clips = []
    for i, track in enumerate(song.tracks):
        if scene_index < len(track.clip_slots):
            slot = track.clip_slots[scene_index]
            clip_info = {
                "track_index": i,
                "track_name": track.name,
                "has_clip": slot.has_clip,
                "clip_name": slot.clip.name if slot.has_clip else None,
                "is_playing": slot.is_playing,
                "is_recording": slot.is_recording,
                "is_triggered": slot.is_triggered,
                "color": slot.clip.color if slot.has_clip else None,
            }
            clips.append(clip_info)

    return {"scene_index": scene_index, "clips": clips}


READ_HANDLERS = {
    "get_session_info": get_session_info,
    "get_livemcp_info": get_livemcp_info,
    "get_song_time": get_song_time,
    "get_cue_points": get_cue_points,
    "get_selected_track": get_selected_track,
    "get_selected_scene": get_selected_scene,
    "get_scene_properties": get_scene_properties,
    "get_application_info": get_application_info,
    "get_application_dialog": get_application_dialog,
    "get_application_cpu_usage": get_application_cpu_usage,
    "get_available_main_views": get_available_main_views,
    "is_view_visible": is_view_visible,
    "get_record_mode": get_record_mode,
    "get_link_state": get_link_state,
    "get_count_in_state": get_count_in_state,
    "get_session_record_status": get_session_record_status,
    "get_view_state": get_view_state,
    "get_selected_device": get_selected_device,
    "get_selected_parameter": get_selected_parameter,
    "get_selected_chain": get_selected_chain,
    "get_punch_state": get_punch_state,
    "get_session_automation_record": get_session_automation_record,
    "get_session_metadata": get_session_metadata,
    "get_song_smpte_time": get_song_smpte_time,
    "get_scene_info": get_scene_info,
    "get_scene_clips": get_scene_clips,
}

WRITE_HANDLERS = {
    "set_tempo": set_tempo,
    "start_playback": start_playback,
    "stop_playback": stop_playback,
    "undo": undo,
    "redo": redo,
    "set_time_signature": set_time_signature,
    "set_loop_region": set_loop_region,
    "set_song_time": set_song_time,
    "continue_playing": continue_playing,
    "stop_all_clips": stop_all_clips,
    "capture_midi": capture_midi,
    "set_metronome": set_metronome,
    "set_groove_amount": set_groove_amount,
    "set_scale": set_scale,
    "jump_to_next_cue": jump_to_next_cue,
    "jump_to_prev_cue": jump_to_prev_cue,
    "jump_to_cue": jump_to_cue,
    "set_midi_recording_quantization": set_midi_recording_quantization,
    "set_clip_trigger_quantization": set_clip_trigger_quantization,
    "trigger_record": trigger_record,
    "tap_tempo": tap_tempo,
    "set_selected_track": set_selected_track,
    "set_selected_scene": set_selected_scene,
    "set_scene_tempo": set_scene_tempo,
    "set_scene_time_signature": set_scene_time_signature,
    "press_current_dialog_button": press_current_dialog_button,
    "show_view": show_view,
    "hide_view": hide_view,
    "focus_view": focus_view,
    "toggle_browse": toggle_browse,
    "set_ableton_link_enabled": set_ableton_link_enabled,
    "set_ableton_link_start_stop_sync_enabled": set_ableton_link_start_stop_sync_enabled,
    "set_tempo_follower_enabled": set_tempo_follower_enabled,
    "set_session_record": set_session_record,
    "set_record_mode": set_record_mode,
    "capture_and_insert_scene": capture_and_insert_scene,
    "create_locator": create_locator,
    "delete_locator": delete_locator,
    "select_device": select_device,
    "set_follow_song": set_follow_song,
    "set_draw_mode": set_draw_mode,
    "select_clip_in_detail": select_clip_in_detail,
    "set_punch_in": set_punch_in,
    "set_punch_out": set_punch_out,
    "re_enable_automation": re_enable_automation,
    "set_session_automation_record": set_session_automation_record,
    "show_message": show_message,
}
