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
}
