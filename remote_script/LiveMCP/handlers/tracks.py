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
        "is_frozen": track.is_frozen,
        "can_be_frozen": track.can_be_frozen,
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


def get_track_routing(control_surface, params):
    """Return routing info for a specific track."""
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]

    available_input_types = [t.display_name for t in track.available_input_routing_types]
    available_output_types = [t.display_name for t in track.available_output_routing_types]

    return {
        "track_index": track_index,
        "input_routing_type": track.input_routing_type.display_name,
        "input_routing_channel": track.input_routing_channel.display_name,
        "output_routing_type": track.output_routing_type.display_name,
        "output_routing_channel": track.output_routing_channel.display_name,
        "available_input_routing_types": available_input_types,
        "available_output_routing_types": available_output_types,
    }


def get_group_info(control_surface, params):
    """Return group/fold info for a specific track."""
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]
    is_foldable = track.is_foldable
    is_grouped = track.is_grouped

    result = {
        "track_index": track_index,
        "is_foldable": is_foldable,
        "is_grouped": is_grouped,
        "fold_state": track.fold_state if is_foldable else None,
    }

    if is_grouped:
        result["group_track_name"] = track.group_track.name

    return result


def duplicate_track(control_surface, params):
    """Duplicate a track by index."""
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    song.duplicate_track(track_index)
    return {"duplicated_track_index": track_index}


def duplicate_scene(control_surface, params):
    """Duplicate a scene by index."""
    scene_index = params.get("scene_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    scene_index = int(scene_index)
    song = control_surface.song()

    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))

    song.duplicate_scene(scene_index)
    return {"duplicated_scene_index": scene_index}


def delete_scene(control_surface, params):
    """Delete a scene by index."""
    scene_index = params.get("scene_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    scene_index = int(scene_index)
    song = control_surface.song()

    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))

    song.delete_scene(scene_index)
    return {"deleted_scene_index": scene_index}


def set_track_color(control_surface, params):
    """Set the color index of a track."""
    track_index = params.get("track_index")
    color_index = params.get("color_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if color_index is None:
        raise ValueError("Missing required parameter: color_index")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    song.tracks[track_index].color_index = int(color_index)
    return {"track_index": track_index, "color_index": int(color_index)}


def set_scene_name(control_surface, params):
    """Set the name of a scene."""
    scene_index = params.get("scene_index")
    name = params.get("name")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    if name is None:
        raise ValueError("Missing required parameter: name")
    scene_index = int(scene_index)
    song = control_surface.song()

    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))

    song.scenes[scene_index].name = str(name)
    return {"scene_index": scene_index, "name": str(name)}


def set_scene_color(control_surface, params):
    """Set the color index of a scene."""
    scene_index = params.get("scene_index")
    color_index = params.get("color_index")
    if scene_index is None:
        raise ValueError("Missing required parameter: scene_index")
    if color_index is None:
        raise ValueError("Missing required parameter: color_index")
    scene_index = int(scene_index)
    song = control_surface.song()

    if scene_index < 0 or scene_index >= len(song.scenes):
        raise ValueError("Scene index {0} out of range (0-{1})".format(
            scene_index, len(song.scenes) - 1))

    song.scenes[scene_index].color_index = int(color_index)
    return {"scene_index": scene_index, "color_index": int(color_index)}


def create_return_track(control_surface, params):
    """Create a new return track."""
    song = control_surface.song()
    song.create_return_track()
    return {"return_track_count": len(song.return_tracks)}


def delete_return_track(control_surface, params):
    """Delete a return track by index."""
    return_index = params.get("return_index")
    if return_index is None:
        raise ValueError("Missing required parameter: return_index")
    return_index = int(return_index)
    song = control_surface.song()

    if return_index < 0 or return_index >= len(song.return_tracks):
        raise ValueError("Return track index {0} out of range (0-{1})".format(
            return_index, len(song.return_tracks) - 1))

    song.delete_return_track(return_index)
    return {"deleted_return_index": return_index}


def set_track_monitoring(control_surface, params):
    """Set the monitoring state of a track (0=In, 1=Auto, 2=Off)."""
    track_index = params.get("track_index")
    state = params.get("state")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if state is None:
        raise ValueError("Missing required parameter: state")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    song.tracks[track_index].current_monitoring_state = int(state)
    return {"track_index": track_index, "monitoring_state": int(state)}


def set_track_input_routing(control_surface, params):
    """Set the input routing type and optionally channel for a track."""
    track_index = params.get("track_index")
    routing_type_name = params.get("routing_type_name")
    routing_channel_name = params.get("routing_channel_name")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if routing_type_name is None:
        raise ValueError("Missing required parameter: routing_type_name")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]

    matched_type = None
    for rt in track.available_input_routing_types:
        if rt.display_name == routing_type_name:
            matched_type = rt
            break
    if matched_type is None:
        raise ValueError("Input routing type '{0}' not found".format(routing_type_name))

    track.input_routing_type = matched_type

    if routing_channel_name is not None:
        matched_channel = None
        for ch in track.available_input_routing_channels:
            if ch.display_name == routing_channel_name:
                matched_channel = ch
                break
        if matched_channel is None:
            raise ValueError("Input routing channel '{0}' not found".format(routing_channel_name))
        track.input_routing_channel = matched_channel

    return {
        "track_index": track_index,
        "input_routing_type": track.input_routing_type.display_name,
        "input_routing_channel": track.input_routing_channel.display_name,
    }


def set_track_output_routing(control_surface, params):
    """Set the output routing type and optionally channel for a track."""
    track_index = params.get("track_index")
    routing_type_name = params.get("routing_type_name")
    routing_channel_name = params.get("routing_channel_name")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if routing_type_name is None:
        raise ValueError("Missing required parameter: routing_type_name")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]

    matched_type = None
    for rt in track.available_output_routing_types:
        if rt.display_name == routing_type_name:
            matched_type = rt
            break
    if matched_type is None:
        raise ValueError("Output routing type '{0}' not found".format(routing_type_name))

    track.output_routing_type = matched_type

    if routing_channel_name is not None:
        matched_channel = None
        for ch in track.available_output_routing_channels:
            if ch.display_name == routing_channel_name:
                matched_channel = ch
                break
        if matched_channel is None:
            raise ValueError("Output routing channel '{0}' not found".format(routing_channel_name))
        track.output_routing_channel = matched_channel

    return {
        "track_index": track_index,
        "output_routing_type": track.output_routing_type.display_name,
        "output_routing_channel": track.output_routing_channel.display_name,
    }


def fold_track(control_surface, params):
    """Fold or unfold a group track."""
    track_index = params.get("track_index")
    fold = params.get("fold")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if fold is None:
        raise ValueError("Missing required parameter: fold")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]
    if not track.is_foldable:
        raise ValueError("Track {0} is not a group track and cannot be folded".format(track_index))

    track.fold_state = int(fold)
    return {"track_index": track_index, "fold_state": int(fold)}


def get_all_tracks_info(control_surface, params):
    """Return summary info for all tracks at once."""
    song = control_surface.song()
    tracks = []
    for i, track in enumerate(song.tracks):
        clip_count = sum(1 for slot in track.clip_slots if slot.has_clip)
        track_type = "midi" if track.has_midi_input else ("audio" if track.has_audio_input else "unknown")
        tracks.append({
            "index": i,
            "name": track.name,
            "type": track_type,
            "color_index": track.color_index,
            "mute": track.mute,
            "solo": track.solo,
            "arm": track.arm,
            "is_foldable": track.is_foldable,
            "is_grouped": track.is_grouped,
            "device_count": len(track.devices),
            "clip_count": clip_count,
        })
    return {"tracks": tracks, "track_count": len(tracks)}


def get_track_freeze_status(control_surface, params):
    """Get freeze status of a track."""
    song = control_surface.song()
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)
    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range".format(track_index))
    track = song.tracks[track_index]
    return {
        "track_index": track_index,
        "name": track.name,
        "is_frozen": track.is_frozen,
        "can_be_frozen": track.can_be_frozen,
    }


def get_track_output_meter(control_surface, params):
    """Get the output meter levels for a track."""
    song = control_surface.song()
    track_index = params.get("track_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    track_index = int(track_index)
    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))
    track = song.tracks[track_index]
    result = {
        "track_index": track_index,
        "output_meter_level": track.output_meter_level,
    }
    if track.has_audio_output:
        result["output_meter_left"] = track.output_meter_left
        result["output_meter_right"] = track.output_meter_right
    return result


def get_clip_slot_status(control_surface, params):
    """Get detailed status of a specific clip slot."""
    song = control_surface.song()
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
        raise ValueError("Clip slot index {0} out of range (0-{1})".format(
            clip_index, len(track.clip_slots) - 1))
    slot = track.clip_slots[clip_index]
    result = {
        "track_index": track_index,
        "clip_index": clip_index,
        "has_clip": slot.has_clip,
        "is_playing": slot.is_playing,
        "is_recording": slot.is_recording,
        "is_triggered": slot.is_triggered,
        "color": slot.color,
        "color_index": slot.color_index,
    }
    if slot.has_clip:
        clip = slot.clip
        result["clip_name"] = clip.name
        result["clip_length"] = clip.length
        result["clip_color"] = clip.color
    return result


def get_return_track_sends(control_surface, params):
    """Get the send values for a return track."""
    song = control_surface.song()
    return_index = params.get("return_index")
    if return_index is None:
        raise ValueError("Missing required parameter: return_index")
    return_index = int(return_index)
    returns = song.return_tracks
    if return_index < 0 or return_index >= len(returns):
        raise ValueError("Return track index out of range")
    track = returns[return_index]
    sends = []
    for i, send in enumerate(track.mixer_device.sends):
        sends.append({"index": i, "name": send.name, "value": send.value})
    return {"return_index": return_index, "name": track.name, "sends": sends}


def set_clip_slot_color(control_surface, params):
    """Set the color of a clip slot."""
    song = control_surface.song()
    track_index = params.get("track_index")
    clip_index = params.get("clip_index")
    color = params.get("color")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if clip_index is None:
        raise ValueError("Missing required parameter: clip_index")
    if color is None:
        raise ValueError("Missing required parameter: color")
    track_index = int(track_index)
    clip_index = int(clip_index)
    color = int(color)
    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))
    track = song.tracks[track_index]
    if clip_index < 0 or clip_index >= len(track.clip_slots):
        raise ValueError("Clip slot index {0} out of range (0-{1})".format(
            clip_index, len(track.clip_slots) - 1))
    track.clip_slots[clip_index].color = color
    return {"track_index": track_index, "clip_index": clip_index, "color": color}


def set_return_track_send(control_surface, params):
    """Set a send value on a return track."""
    song = control_surface.song()
    return_index = params.get("return_index")
    send_index = params.get("send_index")
    value = params.get("value")
    if return_index is None:
        raise ValueError("Missing required parameter: return_index")
    if send_index is None:
        raise ValueError("Missing required parameter: send_index")
    if value is None:
        raise ValueError("Missing required parameter: value")
    return_index = int(return_index)
    send_index = int(send_index)
    value = float(value)
    returns = song.return_tracks
    if return_index < 0 or return_index >= len(returns):
        raise ValueError("Return track index {0} out of range (0-{1})".format(
            return_index, len(returns) - 1))
    sends = returns[return_index].mixer_device.sends
    if send_index < 0 or send_index >= len(sends):
        raise ValueError("Send index {0} out of range (0-{1})".format(
            send_index, len(sends) - 1))
    sends[send_index].value = value
    return {"return_index": return_index, "send_index": send_index, "value": value}


def set_track_properties(control_surface, params):
    """Set multiple track properties in one call."""
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
    result = {"track_index": track_index}

    if "name" in params:
        track.name = str(params["name"])
        result["name"] = track.name
    if "volume" in params:
        mixer.volume.value = float(params["volume"])
        result["volume"] = mixer.volume.value
    if "pan" in params:
        mixer.panning.value = float(params["pan"])
        result["pan"] = mixer.panning.value
    if "mute" in params:
        track.mute = bool(params["mute"])
        result["mute"] = track.mute
    if "solo" in params:
        track.solo = bool(params["solo"])
        result["solo"] = track.solo
    if "arm" in params:
        track.arm = bool(params["arm"])
        result["arm"] = track.arm
    if "color" in params:
        track.color_index = int(params["color"])
        result["color"] = track.color_index

    return result


READ_HANDLERS = {
    "get_track_info": get_track_info,
    "get_return_tracks": get_return_tracks,
    "get_track_routing": get_track_routing,
    "get_group_info": get_group_info,
    "get_all_tracks_info": get_all_tracks_info,
    "get_track_freeze_status": get_track_freeze_status,
    "get_clip_slot_status": get_clip_slot_status,
    "get_return_track_sends": get_return_track_sends,
}

WRITE_HANDLERS = {
    "get_track_output_meter": get_track_output_meter,
    "create_midi_track": create_midi_track,
    "create_audio_track": create_audio_track,
    "set_track_name": set_track_name,
    "delete_track": delete_track,
    "duplicate_track": duplicate_track,
    "duplicate_scene": duplicate_scene,
    "delete_scene": delete_scene,
    "set_track_color": set_track_color,
    "set_scene_name": set_scene_name,
    "set_scene_color": set_scene_color,
    "create_return_track": create_return_track,
    "delete_return_track": delete_return_track,
    "set_track_monitoring": set_track_monitoring,
    "set_track_input_routing": set_track_input_routing,
    "set_track_output_routing": set_track_output_routing,
    "fold_track": fold_track,
    "set_clip_slot_color": set_clip_slot_color,
    "set_return_track_send": set_return_track_send,
    "set_track_properties": set_track_properties,
}
