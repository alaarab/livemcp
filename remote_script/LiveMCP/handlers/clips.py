"""Clip handlers: MIDI notes, clip management, scenes."""


def _get_track_and_clip(song, params):
    """Validate and return (track, clip_slot, clip) from params."""
    track_index = params.get("track_index")
    clip_index = params.get("clip_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if clip_index is None:
        raise ValueError("Missing required parameter: clip_index")
    track_index = int(track_index)
    clip_index = int(clip_index)

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]

    if clip_index < 0 or clip_index >= len(track.clip_slots):
        raise ValueError("Clip index {0} out of range (0-{1})".format(
            clip_index, len(track.clip_slots) - 1))

    slot = track.clip_slots[clip_index]
    clip = slot.clip if slot.has_clip else None
    return track, slot, clip


def get_notes_from_clip(control_surface, params):
    """Get all MIDI notes from a clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    raw_notes = clip.get_notes_extended(0, 128, 0.0, clip.length)
    notes = []
    for note in raw_notes:
        notes.append({
            "pitch": note.pitch,
            "start_time": note.start_time,
            "duration": note.duration,
            "velocity": note.velocity,
            "mute": note.mute,
        })

    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "clip_name": clip.name,
        "clip_length": clip.length,
        "note_count": len(notes),
        "notes": notes,
    }


def create_clip(control_surface, params):
    """Create a new MIDI clip in a clip slot."""
    song = control_surface.song()
    track, slot, existing_clip = _get_track_and_clip(song, params)
    length = float(params.get("length", 4.0))

    if existing_clip is not None:
        raise ValueError("Clip slot already contains a clip")

    slot.create_clip(length)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "length": length,
    }


def set_clip_name(control_surface, params):
    """Set the name of a clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)
    name = params.get("name")
    if name is None:
        raise ValueError("Missing required parameter: name")
    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    clip.name = str(name)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "name": str(name),
    }


def delete_clip(control_surface, params):
    """Delete a clip from a clip slot."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    slot.delete_clip()
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "deleted": True,
    }


def add_notes_to_clip(control_surface, params):
    """Add MIDI notes to a clip using set_notes(tuple)."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    notes_data = params.get("notes")
    if not notes_data:
        raise ValueError("Missing required parameter: notes")

    note_tuples = []
    for n in notes_data:
        pitch = int(n.get("pitch", 60))
        start_time = float(n.get("start_time", 0.0))
        duration = float(n.get("duration", 0.25))
        velocity = int(n.get("velocity", 100))
        mute = bool(n.get("mute", False))
        note_tuples.append((pitch, start_time, duration, velocity, mute))

    clip.set_notes(tuple(note_tuples))
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "notes_added": len(note_tuples),
    }


def fire_clip(control_surface, params):
    """Start playing a clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    slot.fire()
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "fired": True,
    }


def stop_clip(control_surface, params):
    """Stop playing a clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    slot.stop()
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "stopped": True,
    }


def fire_scene(control_surface, params):
    """Fire (launch) a scene by index."""
    scene_index = params.get("scene_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    scene_index = int(scene_index)
    song = control_surface.song()

    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))

    song.scenes[scene_index].fire()
    return {"scene_index": scene_index, "fired": True}


def create_scene(control_surface, params):
    """Create a new scene at the given index."""
    song = control_surface.song()
    index = int(params.get("index", -1))
    if index < 0:
        index = len(song.scenes)
    song.create_scene(index)
    return {"scene_index": index}


def get_scene_info(control_surface, params):
    """Get info about a specific scene."""
    scene_index = params.get("scene_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    scene_index = int(scene_index)
    song = control_surface.song()

    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))

    scene = song.scenes[scene_index]
    clip_info = []
    for i, track in enumerate(song.tracks):
        if scene_index < len(track.clip_slots):
            slot = track.clip_slots[scene_index]
            clip_info.append({
                "track_index": i,
                "track_name": track.name,
                "has_clip": slot.has_clip,
                "clip_name": slot.clip.name if slot.has_clip else None,
            })

    return {
        "scene_index": scene_index,
        "name": scene.name,
        "color_index": scene.color_index,
        "clip_count": sum(1 for c in clip_info if c["has_clip"]),
        "clips": clip_info,
    }


def remove_notes_from_clip(control_surface, params):
    """Remove MIDI notes from a clip within a pitch/time range."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    from_pitch = int(params.get("from_pitch", 0))
    pitch_span = int(params.get("pitch_span", 128))
    from_time = float(params.get("from_time", 0.0))
    time_span = params.get("time_span")
    if time_span is None:
        time_span = clip.length
    else:
        time_span = float(time_span)

    clip.remove_notes_extended(from_pitch, pitch_span, from_time, time_span)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "from_pitch": from_pitch,
        "pitch_span": pitch_span,
        "from_time": from_time,
        "time_span": time_span,
    }


def clear_clip_notes(control_surface, params):
    """Remove all MIDI notes from a clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    clip.remove_notes_extended(0, 128, 0.0, clip.length)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "cleared": True,
    }


def set_clip_loop(control_surface, params):
    """Set clip loop properties."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    result = {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
    }

    if "looping" in params:
        clip.looping = bool(params["looping"])
        result["looping"] = clip.looping
    if "loop_start" in params:
        clip.loop_start = float(params["loop_start"])
        result["loop_start"] = clip.loop_start
    if "loop_end" in params:
        clip.loop_end = float(params["loop_end"])
        result["loop_end"] = clip.loop_end
    if "start_marker" in params:
        clip.start_marker = float(params["start_marker"])
        result["start_marker"] = clip.start_marker
    if "end_marker" in params:
        clip.end_marker = float(params["end_marker"])
        result["end_marker"] = clip.end_marker

    return result


def duplicate_clip(control_surface, params):
    """Duplicate a clip to a target clip slot."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    target_track_index = params.get("target_track_index")
    target_clip_index = params.get("target_clip_index")
    if target_track_index is None:
        raise ValueError("Missing required parameter: target_track_index")
    if target_clip_index is None:
        raise ValueError("Missing required parameter: target_clip_index")
    target_track_index = int(target_track_index)
    target_clip_index = int(target_clip_index)

    if target_track_index < 0 or target_track_index >= len(song.tracks):
        raise ValueError("Target track index {0} out of range (0-{1})".format(
            target_track_index, len(song.tracks) - 1))

    target_track = song.tracks[target_track_index]
    if target_clip_index < 0 or target_clip_index >= len(target_track.clip_slots):
        raise ValueError("Target clip index {0} out of range (0-{1})".format(
            target_clip_index, len(target_track.clip_slots) - 1))

    target_slot = target_track.clip_slots[target_clip_index]
    slot.duplicate_clip_to(target_slot)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "target_track_index": target_track_index,
        "target_clip_index": target_clip_index,
        "duplicated": True,
    }


def set_clip_color(control_surface, params):
    """Set the color of a clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    color_index = params.get("color_index")
    if color_index is None:
        raise ValueError("Missing required parameter: color_index")

    clip.color_index = int(color_index)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "color_index": int(color_index),
    }


def quantize_clip(control_surface, params):
    """Quantize notes in a clip to a grid."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    grid = params.get("grid")
    if grid is None:
        raise ValueError("Missing required parameter: grid")
    grid = float(grid)
    amount = float(params.get("amount", 1.0))

    clip.quantize(grid, amount)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "grid": grid,
        "amount": amount,
    }


def duplicate_clip_loop(control_surface, params):
    """Duplicate the loop content of a clip, doubling its length."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    clip.duplicate_loop()
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "duplicated_loop": True,
    }


def crop_clip(control_surface, params):
    """Crop a clip to its loop boundaries."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    clip.crop()
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "cropped": True,
    }


def set_clip_muted(control_surface, params):
    """Set whether a clip is muted (deactivated)."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    muted = params.get("muted")
    if muted is None:
        raise ValueError("Missing required parameter: muted")

    clip.muted = bool(muted)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "muted": clip.muted,
    }


def set_clip_gain(control_surface, params):
    """Set the gain of an audio clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    gain = params.get("gain")
    if gain is None:
        raise ValueError("Missing required parameter: gain")

    clip.gain = float(gain)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "gain": float(gain),
    }


def set_clip_pitch(control_surface, params):
    """Set the pitch transposition of an audio clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    result = {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
    }

    if "coarse" in params:
        clip.pitch_coarse = int(params["coarse"])
        result["pitch_coarse"] = clip.pitch_coarse
    if "fine" in params:
        clip.pitch_fine = float(params["fine"])
        result["pitch_fine"] = clip.pitch_fine

    return result


def set_clip_launch_mode(control_surface, params):
    """Set the launch mode of a clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    mode = params.get("mode")
    if mode is None:
        raise ValueError("Missing required parameter: mode")

    clip.launch_mode = int(mode)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "launch_mode": int(mode),
    }


def set_clip_warp_mode(control_surface, params):
    """Set the warp mode of an audio clip."""
    song = control_surface.song()
    track, slot, clip = _get_track_and_clip(song, params)

    if clip is None:
        raise ValueError("No clip in track {0}, slot {1}".format(
            params["track_index"], params["clip_index"]))

    warp_mode = params.get("warp_mode")
    if warp_mode is None:
        raise ValueError("Missing required parameter: warp_mode")

    clip.warp_mode = int(warp_mode)
    return {
        "track_index": int(params["track_index"]),
        "clip_index": int(params["clip_index"]),
        "warp_mode": int(warp_mode),
    }


READ_HANDLERS = {
    "get_notes_from_clip": get_notes_from_clip,
    "get_scene_info": get_scene_info,
}

WRITE_HANDLERS = {
    "create_clip": create_clip,
    "set_clip_name": set_clip_name,
    "delete_clip": delete_clip,
    "add_notes_to_clip": add_notes_to_clip,
    "fire_clip": fire_clip,
    "stop_clip": stop_clip,
    "fire_scene": fire_scene,
    "create_scene": create_scene,
    "remove_notes_from_clip": remove_notes_from_clip,
    "clear_clip_notes": clear_clip_notes,
    "set_clip_loop": set_clip_loop,
    "duplicate_clip": duplicate_clip,
    "set_clip_color": set_clip_color,
    "quantize_clip": quantize_clip,
    "duplicate_clip_loop": duplicate_clip_loop,
    "crop_clip": crop_clip,
    "set_clip_muted": set_clip_muted,
    "set_clip_gain": set_clip_gain,
    "set_clip_pitch": set_clip_pitch,
    "set_clip_launch_mode": set_clip_launch_mode,
    "set_clip_warp_mode": set_clip_warp_mode,
}
