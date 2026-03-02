"""Session-level handlers: tempo, transport, time signature."""


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
        except Exception as e:
            pass
        try:
            result["scale_name"] = song.scale_name
        except Exception as e:
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
    scene_index = int(params.get("scene_index"))
    tempo = float(params.get("tempo"))
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
    scene_index = int(params.get("scene_index"))
    numerator = int(params.get("numerator"))
    denominator = int(params.get("denominator"))
    scene = song.scenes[scene_index]
    scene.time_signature_numerator = numerator
    scene.time_signature_denominator = denominator
    return {"scene_index": scene_index, "numerator": numerator, "denominator": denominator}


READ_HANDLERS = {
    "get_session_info": get_session_info,
    "get_song_time": get_song_time,
    "get_cue_points": get_cue_points,
    "get_selected_track": get_selected_track,
    "get_selected_scene": get_selected_scene,
    "get_scene_properties": get_scene_properties,
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
}
