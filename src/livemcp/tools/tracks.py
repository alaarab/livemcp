"""Track tools: info, creation, naming, deletion."""

import json

from ..connection import get_connection


def get_track_info(track_index: int) -> str:
    """Get detailed information about a specific track.

    Returns the track name, type, mute/solo/arm state, volume, pan,
    list of clip slots with clip info, and list of devices.

    Args:
        track_index: Zero-based index of the track.
    """
    result = get_connection().send_command("get_track_info", {"track_index": track_index})
    return json.dumps(result)


def create_midi_track(index: int = -1) -> str:
    """Create a new MIDI track in the session.

    Args:
        index: Position to insert the track. Use -1 to append at the end.
    """
    result = get_connection().send_command("create_midi_track", {"index": index})
    return json.dumps(result)


def create_audio_track(index: int = -1) -> str:
    """Create a new audio track in the session.

    Args:
        index: Position to insert the track. Use -1 to append at the end.
    """
    result = get_connection().send_command("create_audio_track", {"index": index})
    return json.dumps(result)


def set_track_name(track_index: int, name: str) -> str:
    """Set the name of a track.

    Args:
        track_index: Zero-based index of the track.
        name: New name for the track.
    """
    result = get_connection().send_command("set_track_name", {
        "track_index": track_index,
        "name": name,
    })
    return json.dumps(result)


def delete_track(track_index: int) -> str:
    """Delete a track from the session.

    Args:
        track_index: Zero-based index of the track to delete.
    """
    result = get_connection().send_command("delete_track", {"track_index": track_index})
    return json.dumps(result)


def get_return_tracks() -> str:
    """Get information about all return tracks in the session.

    Returns a list of return tracks with name, mute, solo, volume, and pan.
    """
    result = get_connection().send_command("get_return_tracks", {})
    return json.dumps(result)


def get_track_routing(track_index: int) -> str:
    """Get the input and output routing configuration for a track.

    Returns input/output routing type and channel display names, plus lists
    of all available input and output routing types.

    Args:
        track_index: Zero-based index of the track.
    """
    result = get_connection().send_command("get_track_routing", {"track_index": track_index})
    return json.dumps(result)


def get_group_info(track_index: int) -> str:
    """Get group and fold information for a track.

    Returns whether the track is foldable, whether it belongs to a group,
    its current fold state, and the group track name if grouped.

    Args:
        track_index: Zero-based index of the track.
    """
    result = get_connection().send_command("get_group_info", {"track_index": track_index})
    return json.dumps(result)


def duplicate_track(track_index: int) -> str:
    """Duplicate a track.

    Args:
        track_index: Zero-based index of the track to duplicate.
    """
    result = get_connection().send_command("duplicate_track", {"track_index": track_index})
    return json.dumps(result)


def duplicate_scene(scene_index: int) -> str:
    """Duplicate a scene.

    Args:
        scene_index: Zero-based index of the scene to duplicate.
    """
    result = get_connection().send_command("duplicate_scene", {"scene_index": scene_index})
    return json.dumps(result)


def delete_scene(scene_index: int) -> str:
    """Delete a scene from the session.

    Args:
        scene_index: Zero-based index of the scene to delete.
    """
    result = get_connection().send_command("delete_scene", {"scene_index": scene_index})
    return json.dumps(result)


def set_track_color(track_index: int, color_index: int) -> str:
    """Set the color of a track by color index.

    Args:
        track_index: Zero-based index of the track.
        color_index: Ableton color palette index.
    """
    result = get_connection().send_command("set_track_color", {
        "track_index": track_index,
        "color_index": color_index,
    })
    return json.dumps(result)


def set_scene_name(scene_index: int, name: str) -> str:
    """Set the name of a scene.

    Args:
        scene_index: Zero-based index of the scene.
        name: New name for the scene.
    """
    result = get_connection().send_command("set_scene_name", {
        "scene_index": scene_index,
        "name": name,
    })
    return json.dumps(result)


def set_scene_color(scene_index: int, color_index: int) -> str:
    """Set the color of a scene by color index.

    Args:
        scene_index: Zero-based index of the scene.
        color_index: Ableton color palette index.
    """
    result = get_connection().send_command("set_scene_color", {
        "scene_index": scene_index,
        "color_index": color_index,
    })
    return json.dumps(result)


def create_return_track() -> str:
    """Create a new return track in the session."""
    result = get_connection().send_command("create_return_track", {})
    return json.dumps(result)


def delete_return_track(return_index: int) -> str:
    """Delete a return track from the session.

    Args:
        return_index: Zero-based index of the return track to delete.
    """
    result = get_connection().send_command("delete_return_track", {"return_index": return_index})
    return json.dumps(result)


def set_track_monitoring(track_index: int, state: int) -> str:
    """Set the monitoring state of a track.

    Args:
        track_index: Zero-based index of the track.
        state: Monitoring state (0=In, 1=Auto, 2=Off).
    """
    result = get_connection().send_command("set_track_monitoring", {
        "track_index": track_index,
        "state": state,
    })
    return json.dumps(result)


def set_track_input_routing(track_index: int, routing_type_name: str, routing_channel_name: str = None) -> str:
    """Set the input routing for a track.

    Use get_track_routing to see available routing type names.

    Args:
        track_index: Zero-based index of the track.
        routing_type_name: Display name of the desired input routing type.
        routing_channel_name: Display name of the desired input routing channel (optional).
    """
    params = {"track_index": track_index, "routing_type_name": routing_type_name}
    if routing_channel_name is not None:
        params["routing_channel_name"] = routing_channel_name
    result = get_connection().send_command("set_track_input_routing", params)
    return json.dumps(result)


def set_track_output_routing(track_index: int, routing_type_name: str, routing_channel_name: str = None) -> str:
    """Set the output routing for a track.

    Use get_track_routing to see available routing type names.

    Args:
        track_index: Zero-based index of the track.
        routing_type_name: Display name of the desired output routing type.
        routing_channel_name: Display name of the desired output routing channel (optional).
    """
    params = {"track_index": track_index, "routing_type_name": routing_type_name}
    if routing_channel_name is not None:
        params["routing_channel_name"] = routing_channel_name
    result = get_connection().send_command("set_track_output_routing", params)
    return json.dumps(result)


def fold_track(track_index: int, fold: int) -> str:
    """Fold or unfold a group track.

    Args:
        track_index: Zero-based index of the group track.
        fold: 1 to fold (collapse), 0 to unfold (expand).
    """
    result = get_connection().send_command("fold_track", {
        "track_index": track_index,
        "fold": fold,
    })
    return json.dumps(result)


def get_track_freeze_status(track_index: int) -> str:
    """Get the freeze status of a track.

    Args:
        track_index: Zero-based index of the track.

    Returns whether the track is frozen and whether it can be frozen.
    Note: Freezing/flattening cannot be triggered via the API (read-only status).
    """
    result = get_connection().send_command("get_track_freeze_status", {
        "track_index": track_index,
    })
    return json.dumps(result)


def get_all_tracks_info() -> str:
    """Get summary information for all tracks at once.

    Returns a list of all tracks with name, type, color, mute, solo, arm,
    is_foldable, is_grouped, device count, and clip count. Useful for getting
    a full session overview without making separate calls per track.
    """
    result = get_connection().send_command("get_all_tracks_info", {})
    return json.dumps(result)


def get_track_output_meter(track_index: int) -> str:
    """Get the output meter levels for a track.

    Returns the current output meter level, left channel, and right channel values.

    Args:
        track_index: Zero-based index of the track.
    """
    result = get_connection().send_command("get_track_output_meter", {
        "track_index": track_index,
    })
    return json.dumps(result)


def get_clip_slot_status(track_index: int, clip_index: int) -> str:
    """Get detailed status of a specific clip slot.

    Returns playing, recording, and trigger state, color info, and clip
    details (name, length, color) if a clip is present.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
    """
    result = get_connection().send_command("get_clip_slot_status", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


def get_return_track_sends(return_index: int) -> str:
    """Get the send values for a return track.

    Returns the list of sends on a return track with their names and values.

    Args:
        return_index: Zero-based index of the return track.
    """
    result = get_connection().send_command("get_return_track_sends", {
        "return_index": return_index,
    })
    return json.dumps(result)


def set_clip_slot_color(track_index: int, clip_index: int, color: int) -> str:
    """Set the color of a clip slot.

    Args:
        track_index: Zero-based index of the track.
        clip_index: Zero-based index of the clip slot.
        color: Color value (raw integer color, not color index).
    """
    result = get_connection().send_command("set_clip_slot_color", {
        "track_index": track_index,
        "clip_index": clip_index,
        "color": color,
    })
    return json.dumps(result)


def set_return_track_send(return_index: int, send_index: int, value: float) -> str:
    """Set a send value on a return track.

    Args:
        return_index: Zero-based index of the return track.
        send_index: Zero-based index of the send on the return track.
        value: Send value (0.0 to 1.0).
    """
    result = get_connection().send_command("set_return_track_send", {
        "return_index": return_index,
        "send_index": send_index,
        "value": value,
    })
    return json.dumps(result)


def set_track_properties(
    track_index: int,
    name: str = None,
    volume: float = None,
    pan: float = None,
    mute: bool = None,
    solo: bool = None,
    arm: bool = None,
    color: int = None,
) -> str:
    """Set multiple track properties in a single call.

    Only provided properties are changed; omitted ones are left unchanged.

    Args:
        track_index: Zero-based index of the track.
        name: New name for the track.
        volume: Volume value (0.0 to 1.0).
        pan: Pan value (-1.0 left to 1.0 right).
        mute: True to mute, False to unmute.
        solo: True to solo, False to unsolo.
        arm: True to arm for recording, False to disarm.
        color: Ableton color palette index.
    """
    params = {"track_index": track_index}
    if name is not None:
        params["name"] = name
    if volume is not None:
        params["volume"] = volume
    if pan is not None:
        params["pan"] = pan
    if mute is not None:
        params["mute"] = mute
    if solo is not None:
        params["solo"] = solo
    if arm is not None:
        params["arm"] = arm
    if color is not None:
        params["color"] = color
    result = get_connection().send_command("set_track_properties", params)
    return json.dumps(result)


TOOLS = [
    get_track_info,
    create_midi_track,
    create_audio_track,
    set_track_name,
    delete_track,
    get_return_tracks,
    get_track_routing,
    get_group_info,
    duplicate_track,
    duplicate_scene,
    delete_scene,
    set_track_color,
    set_scene_name,
    set_scene_color,
    create_return_track,
    delete_return_track,
    set_track_monitoring,
    set_track_input_routing,
    set_track_output_routing,
    fold_track,
    get_track_freeze_status,
    get_all_tracks_info,
    get_track_output_meter,
    get_clip_slot_status,
    get_return_track_sends,
    set_clip_slot_color,
    set_return_track_send,
    set_track_properties,
]
