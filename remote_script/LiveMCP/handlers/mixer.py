"""Mixer handlers: volume, pan, mute, solo, arm, sends."""


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


def _serialize_sends(mixer):
    """Serialize send levels for a mixer device."""
    sends = []
    for i, send in enumerate(mixer.sends):
        sends.append({
            "index": i,
            "name": send.name,
            "value": send.value,
        })
    return sends


def get_mixer_state(control_surface, params):
    """Get mixer state for all tracks."""
    song = control_surface.song()
    tracks = []
    for i, track in enumerate(song.tracks):
        mixer = track.mixer_device
        tracks.append({
            "index": i,
            "name": track.name,
            "volume": mixer.volume.value,
            "pan": mixer.panning.value,
            "mute": track.mute,
            "solo": track.solo,
            "arm": track.arm,
            "sends": _serialize_sends(mixer),
        })
    return {"tracks": tracks}


def set_track_volume(control_surface, params):
    """Set track volume (0.0 to 1.0)."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)
    value = params.get("volume")
    if value is None:
        raise ValueError("Missing required parameter: volume")
    value = float(value)
    track.mixer_device.volume.value = value
    return {"track_index": track_index, "volume": value}


def set_track_pan(control_surface, params):
    """Set track panning (-1.0 to 1.0)."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)
    value = params.get("pan")
    if value is None:
        raise ValueError("Missing required parameter: pan")
    value = float(value)
    track.mixer_device.panning.value = value
    return {"track_index": track_index, "pan": value}


def set_track_mute(control_surface, params):
    """Set track mute state."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)
    mute = params.get("mute")
    if mute is None:
        raise ValueError("Missing required parameter: mute")
    track.mute = bool(mute)
    return {"track_index": track_index, "mute": track.mute}


def set_track_solo(control_surface, params):
    """Set track solo state."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)
    solo = params.get("solo")
    if solo is None:
        raise ValueError("Missing required parameter: solo")
    track.solo = bool(solo)
    return {"track_index": track_index, "solo": track.solo}


def set_track_arm(control_surface, params):
    """Set track arm (record enable) state."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)
    arm = params.get("arm")
    if arm is None:
        raise ValueError("Missing required parameter: arm")
    track.arm = bool(arm)
    return {"track_index": track_index, "arm": track.arm}


def set_track_send(control_surface, params):
    """Set a track's send level by send index."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)
    send_index = params.get("send_index")
    value = params.get("value")
    if send_index is None:
        raise ValueError("Missing required parameter: send_index")
    if value is None:
        raise ValueError("Missing required parameter: value")
    send_index = int(send_index)
    value = float(value)

    sends = track.mixer_device.sends
    if send_index < 0 or send_index >= len(sends):
        raise ValueError("Send index {0} out of range (0-{1})".format(
            send_index, len(sends) - 1))

    sends[send_index].value = value
    return {"track_index": track_index, "send_index": send_index, "value": value}


def get_master_mixer_state(control_surface, params):
    """Get master track mixer state: volume, pan, crossfader, and devices."""
    song = control_surface.song()
    master = song.master_track
    mixer = master.mixer_device
    devices = []
    for i, device in enumerate(master.devices):
        devices.append({
            "index": i,
            "name": device.name,
            "class_name": device.class_name,
            "is_active": device.is_active,
        })
    return {
        "volume": mixer.volume.value,
        "pan": mixer.panning.value,
        "crossfader": mixer.crossfader.value,
        "devices": devices,
    }


def set_master_volume(control_surface, params):
    """Set the master track volume."""
    value = params.get("volume")
    if value is None:
        raise ValueError("Missing required parameter: volume")
    value = float(value)
    song = control_surface.song()
    song.master_track.mixer_device.volume.value = value
    return {"volume": value}


def set_master_pan(control_surface, params):
    """Set the master track panning."""
    value = params.get("pan")
    if value is None:
        raise ValueError("Missing required parameter: pan")
    value = float(value)
    song = control_surface.song()
    song.master_track.mixer_device.panning.value = value
    return {"pan": value}


def set_crossfade_assign(control_surface, params):
    """Set the crossfade assignment of a track (0=None, 1=A, 2=B)."""
    song = control_surface.song()
    track_index, track = _get_track(song, params)
    assignment = params.get("assignment")
    if assignment is None:
        raise ValueError("Missing required parameter: assignment")
    assignment = int(assignment)
    if assignment not in (0, 1, 2):
        raise ValueError("Assignment must be 0 (None), 1 (A), or 2 (B)")
    track.mixer_device.crossfade_assign = assignment
    return {"track_index": track_index, "crossfade_assign": assignment}


def get_master_output_meter(control_surface, params):
    """Get output meter levels for the master track."""
    master = control_surface.song().master_track
    return {
        "output_meter_level": master.output_meter_level,
        "output_meter_left": master.output_meter_left,
        "output_meter_right": master.output_meter_right,
    }


def get_return_track_output_meter(control_surface, params):
    """Get output meter levels for a return track by index."""
    song = control_surface.song()
    return_index = int(params.get("return_index"))
    returns = song.return_tracks
    if return_index < 0 or return_index >= len(returns):
        raise ValueError("Return track index out of range")
    track = returns[return_index]
    return {
        "return_index": return_index,
        "name": track.name,
        "output_meter_level": track.output_meter_level,
        "output_meter_left": track.output_meter_left,
        "output_meter_right": track.output_meter_right,
    }


def get_all_track_meters(control_surface, params):
    """Get output meter levels for all tracks and the master."""
    song = control_surface.song()
    tracks = []
    for i, track in enumerate(song.tracks):
        entry = {
            "index": i,
            "name": track.name,
            "output_meter_level": track.output_meter_level,
        }
        if track.has_audio_output:
            entry["output_meter_left"] = track.output_meter_left
            entry["output_meter_right"] = track.output_meter_right
        tracks.append(entry)
    master = song.master_track
    return {
        "tracks": tracks,
        "master": {
            "output_meter_level": master.output_meter_level,
            "output_meter_left": master.output_meter_left,
            "output_meter_right": master.output_meter_right,
        }
    }


READ_HANDLERS = {
    "get_mixer_state": get_mixer_state,
    "get_master_mixer_state": get_master_mixer_state,
    "get_master_output_meter": get_master_output_meter,
    "get_return_track_output_meter": get_return_track_output_meter,
    "get_all_track_meters": get_all_track_meters,
}

WRITE_HANDLERS = {
    "set_track_volume": set_track_volume,
    "set_track_pan": set_track_pan,
    "set_track_mute": set_track_mute,
    "set_track_solo": set_track_solo,
    "set_track_arm": set_track_arm,
    "set_track_send": set_track_send,
    "set_master_volume": set_master_volume,
    "set_master_pan": set_master_pan,
    "set_crossfade_assign": set_crossfade_assign,
}
