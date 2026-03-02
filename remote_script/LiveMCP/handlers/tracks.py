"""Track handlers: info, creation, naming, deletion."""


def _get_track_type(track):
    """Determine track type from its properties."""
    if track.has_midi_input:
        return "midi"
    if track.has_audio_input:
        return "audio"
    return "unknown"


def _serialize_clip_slot(slot, slot_index):
    """Serialize a single clip slot."""
    info = {"index": slot_index, "has_clip": slot.has_clip}
    if slot.has_clip:
        clip = slot.clip
        info["clip"] = {
            "name": clip.name,
            "length": clip.length,
            "is_playing": clip.is_playing,
            "is_recording": clip.is_recording,
            "looping": clip.looping,
            "color_index": clip.color_index,
        }
    return info


def _serialize_device(device, device_index):
    """Serialize basic device info."""
    return {
        "index": device_index,
        "name": device.name,
        "class_name": device.class_name,
        "type": str(device.type),
        "is_active": device.is_active,
    }


def get_track_info(control_surface, params):
    """Return detailed info about a specific track."""
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]
    mixer = track.mixer_device

    clip_slots = []
    for i, slot in enumerate(track.clip_slots):
        clip_slots.append(_serialize_clip_slot(slot, i))

    devices = []
    for i, device in enumerate(track.devices):
        devices.append(_serialize_device(device, i))

    return {
        "index": track_index,
        "name": track.name,
        "type": _get_track_type(track),
        "mute": track.mute,
        "solo": track.solo,
        "arm": track.arm,
        "color_index": track.color_index,
        "volume": mixer.volume.value,
        "pan": mixer.panning.value,
        "clip_slots": clip_slots,
        "devices": devices,
    }


def get_return_tracks(control_surface, params):
    """Return info about all return tracks."""
    song = control_surface.song()
    returns = []
    for i, track in enumerate(song.return_tracks):
        mixer = track.mixer_device
        returns.append({
            "index": i,
            "name": track.name,
            "mute": track.mute,
            "solo": track.solo,
            "color_index": track.color_index,
            "volume": mixer.volume.value,
            "pan": mixer.panning.value,
        })
    return {"return_tracks": returns}


def create_midi_track(control_surface, params):
    """Create a new MIDI track at the given index."""
    song = control_surface.song()
    index = int(params.get("index", -1))
    if index < 0:
        index = len(song.tracks)
    song.create_midi_track(index)
    return {"track_index": index, "track_name": song.tracks[index].name}


def create_audio_track(control_surface, params):
    """Create a new audio track at the given index."""
    song = control_surface.song()
    index = int(params.get("index", -1))
    if index < 0:
        index = len(song.tracks)
    song.create_audio_track(index)
    return {"track_index": index, "track_name": song.tracks[index].name}


def set_track_name(control_surface, params):
    """Rename a track."""
    track_index = params.get("track_index")
    name = params.get("name")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if name is None:
        raise ValueError("Missing required parameter: name")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    song.tracks[track_index].name = str(name)
    return {"track_index": track_index, "name": str(name)}


def delete_track(control_surface, params):
    """Delete a track by index."""
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    song.delete_track(track_index)
    return {"deleted_track_index": track_index}


READ_HANDLERS = {
    "get_track_info": get_track_info,
    "get_return_tracks": get_return_tracks,
}

WRITE_HANDLERS = {
    "create_midi_track": create_midi_track,
    "create_audio_track": create_audio_track,
    "set_track_name": set_track_name,
    "delete_track": delete_track,
}
