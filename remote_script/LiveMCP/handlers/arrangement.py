"""Arrangement view handlers: clips, overdub, back to arrangement."""


def _get_track(song, params):
    """Validate and return a track by index."""
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    return track_index, song.tracks[track_index]


def _serialize_clip(clip):
    """Serialize an arrangement clip to a dictionary."""
    return {
        "name": clip.name,
        "start_time": clip.start_time,
        "end_time": clip.end_time,
        "length": clip.length,
        "is_audio_clip": clip.is_audio_clip,
        "is_midi_clip": clip.is_midi_clip,
        "muted": clip.muted,
        "color": clip.color,
        "color_index": clip.color_index,
        "looping": clip.looping,
    }


def get_arrangement_clips(control_surface, params):
    """Get all arrangement clips for a track."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)
    clips = []
    for i, clip in enumerate(track.arrangement_clips):
        clip_info = _serialize_clip(clip)
        clip_info["index"] = i
        clips.append(clip_info)
    return {"track_index": track_index, "clips": clips}


def get_arrangement_length(control_surface, params):
    """Get the total arrangement length (last event time)."""
    song = control_surface.song()
    return {"arrangement_length": song.last_event_time}


def get_arrangement_overdub(control_surface, params):
    """Get the arrangement overdub state."""
    song = control_surface.song()
    return {"arrangement_overdub": song.arrangement_overdub}


def create_arrangement_midi_clip(control_surface, params):
    """Create a MIDI clip in the arrangement view on a track."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)

    start_time = params.get("start_time")
    if start_time is None:
        raise ValueError("Missing required parameter: start_time")
    start_time = float(start_time)

    length = params.get("length")
    if length is None:
        raise ValueError("Missing required parameter: length")
    length = float(length)

    clip = track.create_midi_clip(start_time, length)
    clip_info = _serialize_clip(clip)
    clip_info["track_index"] = track_index
    return clip_info


def create_arrangement_audio_clip(control_surface, params):
    """Create an audio clip in the arrangement view from a file."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)

    file_path = params.get("file_path")
    if file_path is None:
        raise ValueError("Missing required parameter: file_path")

    position = params.get("position")
    if position is None:
        raise ValueError("Missing required parameter: position")
    position = float(position)

    clip = track.create_audio_clip(file_path, position)
    clip_info = _serialize_clip(clip)
    clip_info["track_index"] = track_index
    return clip_info


def duplicate_to_arrangement(control_surface, params):
    """Duplicate a session clip to the arrangement view."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)

    clip_index = params.get("clip_index")
    if clip_index is None:
        raise ValueError("Missing required parameter: clip_index")
    clip_index = int(clip_index)

    if clip_index < 0 or clip_index >= len(track.clip_slots):
        raise ValueError("Clip slot index {0} out of range (0-{1})".format(
            clip_index, len(track.clip_slots) - 1))

    clip_slot = track.clip_slots[clip_index]
    if not clip_slot.has_clip:
        raise ValueError("No clip in slot {0}".format(clip_index))

    time = params.get("time")
    if time is None:
        raise ValueError("Missing required parameter: time")
    time = float(time)

    clip = clip_slot.clip
    new_clip = track.duplicate_clip_to_arrangement(clip, time)
    clip_info = _serialize_clip(new_clip)
    clip_info["track_index"] = track_index
    return clip_info


def delete_arrangement_clip(control_surface, params):
    """Delete a clip from the arrangement view."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)

    arrangement_clip_index = params.get("arrangement_clip_index")
    if arrangement_clip_index is None:
        raise ValueError("Missing required parameter: arrangement_clip_index")
    arrangement_clip_index = int(arrangement_clip_index)

    arrangement_clips = track.arrangement_clips
    if arrangement_clip_index < 0 or arrangement_clip_index >= len(arrangement_clips):
        raise ValueError("Arrangement clip index {0} out of range (0-{1})".format(
            arrangement_clip_index, len(arrangement_clips) - 1))

    clip = arrangement_clips[arrangement_clip_index]
    track.delete_clip(clip)
    return {"track_index": track_index, "deleted_clip_index": arrangement_clip_index}


def set_arrangement_overdub(control_surface, params):
    """Set the arrangement overdub state."""
    song = control_surface.song()
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    song.arrangement_overdub = bool(enabled)
    return {"arrangement_overdub": song.arrangement_overdub}


def trigger_back_to_arrangement(control_surface, params):
    """Trigger back to arrangement (deactivate session clip playback)."""
    song = control_surface.song()
    song.back_to_arranger = True
    return {"triggered": True}


READ_HANDLERS = {
    "get_arrangement_clips": get_arrangement_clips,
    "get_arrangement_length": get_arrangement_length,
    "get_arrangement_overdub": get_arrangement_overdub,
}

WRITE_HANDLERS = {
    "create_arrangement_midi_clip": create_arrangement_midi_clip,
    "create_arrangement_audio_clip": create_arrangement_audio_clip,
    "duplicate_to_arrangement": duplicate_to_arrangement,
    "delete_arrangement_clip": delete_arrangement_clip,
    "set_arrangement_overdub": set_arrangement_overdub,
    "trigger_back_to_arrangement": trigger_back_to_arrangement,
}
