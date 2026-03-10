"""Device tools: browser navigation, instrument/effect loading, parameter control."""

import json

from ..connection import get_connection


def get_browser_tree(category_type: str = "all") -> str:
    """Get a hierarchical tree of categories from Ableton's browser.

    Args:
        category_type: Filter by type — 'all', 'instruments', 'sounds', 'drums',
                       'audio_effects', or 'midi_effects'.
    """
    result = get_connection().send_command("get_browser_tree", {
        "category_type": category_type,
    })
    return json.dumps(result)


def get_browser_items_at_path(path: str) -> str:
    """Get browser items at a specific path in Ableton's browser.

    Use slash-separated paths like 'instruments/Operator' or 'drums/Kit-Core 909'.

    Args:
        path: Slash-separated path into the browser hierarchy.
    """
    result = get_connection().send_command("get_browser_items_at_path", {"path": path})
    return json.dumps(result)


def load_instrument_or_effect(track_index: int, uri: str) -> str:
    """Load an instrument or effect onto a track using its browser URI.

    Use get_browser_tree or get_browser_items_at_path to discover available URIs.

    Args:
        track_index: Zero-based index of the target track.
        uri: The browser URI of the instrument or effect to load.
    """
    result = get_connection().send_command("load_browser_item", {
        "track_index": track_index,
        "item_uri": uri,
    })
    return json.dumps(result)


def load_drum_kit(track_index: int, rack_uri: str, kit_path: str) -> str:
    """Load a drum rack and then load a specific drum kit into it.

    Args:
        track_index: Zero-based index of the target track.
        rack_uri: URI of the drum rack to load.
        kit_path: Path to the drum kit inside the browser (e.g. 'drums/acoustic/kit1').
    """
    result = get_connection().send_command("load_drum_kit", {
        "track_index": track_index,
        "rack_uri": rack_uri,
        "kit_path": kit_path,
    })
    return json.dumps(result)


def get_device_parameters(track_index: int, device_index: int) -> str:
    """Get all parameters of a device on a track.

    Returns the device name and a list of parameters with name, value, min, and max.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the device in the track's device chain.
    """
    result = get_connection().send_command("get_device_parameters", {
        "track_index": track_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def set_device_parameter(
    track_index: int, device_index: int, parameter_index: int, value: float
) -> str:
    """Set a specific parameter value on a device.

    Use get_device_parameters first to discover available parameters and their ranges.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the device in the track's device chain.
        parameter_index: Zero-based index of the parameter.
        value: New value for the parameter (must be within the parameter's min/max range).
    """
    result = get_connection().send_command("set_device_parameter", {
        "track_index": track_index,
        "device_index": device_index,
        "parameter_index": parameter_index,
        "value": value,
    })
    return json.dumps(result)


def get_master_track_devices() -> str:
    """Get a list of all devices on the master track.

    Returns device index, name, class_name, type, and is_active for each device.
    """
    result = get_connection().send_command("get_master_track_devices", {})
    return json.dumps(result)


def get_return_track_devices(return_index: int) -> str:
    """Get a list of all devices on a return track.

    Args:
        return_index: Zero-based index of the return track.
    """
    result = get_connection().send_command("get_return_track_devices", {
        "return_index": return_index,
    })
    return json.dumps(result)


def get_master_device_parameters(device_index: int) -> str:
    """Get all parameters of a device on the master track.

    Args:
        device_index: Zero-based index of the device in the master track's device chain.
    """
    result = get_connection().send_command("get_master_device_parameters", {
        "device_index": device_index,
    })
    return json.dumps(result)


def get_return_device_parameters(return_index: int, device_index: int) -> str:
    """Get all parameters of a device on a return track.

    Args:
        return_index: Zero-based index of the return track.
        device_index: Zero-based index of the device in the return track's device chain.
    """
    result = get_connection().send_command("get_return_device_parameters", {
        "return_index": return_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def get_device_display_values(track_index: int, device_index: int) -> str:
    """Get all parameters of a device with both raw value and human-readable display value.

    Similar to get_device_parameters but also includes is_enabled and the formatted
    display_value string (e.g. "100 Hz", "-6.0 dB") alongside the raw numeric value.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the device in the track's device chain.
    """
    result = get_connection().send_command("get_device_display_values", {
        "track_index": track_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def get_rack_chains(track_index: int, device_index: int) -> str:
    """Get all chains in an instrument or effect rack device.

    The device must support chains (i.e. be a rack). Returns chain name, mute, solo,
    chain activator, pan, volume, and sends.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the rack device.
    """
    result = get_connection().send_command("get_rack_chains", {
        "track_index": track_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def set_chain_mixer_value(
    track_index: int,
    device_index: int,
    chain_index: int,
    parameter_name: str,
    value: float,
    send_index: int = None,
) -> str:
    """Set a rack chain mixer parameter.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the rack device.
        chain_index: Zero-based index of the chain.
        parameter_name: One of 'chain_activator', 'pan', 'volume', or 'send'.
        value: New value for the target parameter.
        send_index: Zero-based send index when parameter_name is 'send'.
    """
    params = {
        "track_index": track_index,
        "device_index": device_index,
        "chain_index": chain_index,
        "parameter_name": parameter_name,
        "value": value,
    }
    if send_index is not None:
        params["send_index"] = send_index
    result = get_connection().send_command("set_chain_mixer_value", params)
    return json.dumps(result)


def get_drum_chains(track_index: int, device_index: int) -> str:
    """Get drum-chain-specific properties from a Drum Rack.

    Returns each chain's name, mixer values, and drum-specific note/choke settings.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the drum rack device.
    """
    result = get_connection().send_command("get_drum_chains", {
        "track_index": track_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def set_drum_chain_property(
    track_index: int,
    device_index: int,
    chain_index: int,
    property_name: str,
    value: int,
) -> str:
    """Set a drum-chain-specific property.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the drum rack device.
        chain_index: Zero-based index of the drum chain.
        property_name: One of 'in_note', 'out_note', or 'choke_group'.
        value: Integer value for the target property.
    """
    result = get_connection().send_command("set_drum_chain_property", {
        "track_index": track_index,
        "device_index": device_index,
        "chain_index": chain_index,
        "property_name": property_name,
        "value": value,
    })
    return json.dumps(result)


def get_drum_pads(track_index: int, device_index: int) -> str:
    """Get all visible drum pads from a drum rack device.

    Returns pad index, name, MIDI note number, mute, and solo state for each pad.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the drum rack device.
    """
    result = get_connection().send_command("get_drum_pads", {
        "track_index": track_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def delete_device(track_index: int, device_index: int) -> str:
    """Delete a device from a track's device chain.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the device to delete.
    """
    result = get_connection().send_command("delete_device", {
        "track_index": track_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def load_device_on_master(uri: str) -> str:
    """Load a device onto the master track using its browser URI.

    Use get_browser_tree or get_browser_items_at_path to discover available URIs.

    Args:
        uri: The browser URI of the instrument or effect to load.
    """
    result = get_connection().send_command("load_device_on_master", {
        "uri": uri,
    })
    return json.dumps(result)


def load_device_on_return(return_index: int, uri: str) -> str:
    """Load a device onto a return track using its browser URI.

    Use get_browser_tree or get_browser_items_at_path to discover available URIs.

    Args:
        return_index: Zero-based index of the return track.
        uri: The browser URI of the instrument or effect to load.
    """
    result = get_connection().send_command("load_device_on_return", {
        "return_index": return_index,
        "uri": uri,
    })
    return json.dumps(result)


def set_master_device_parameter(device_index: int, parameter_index: int, value: float) -> str:
    """Set a parameter value on a device on the master track.

    Use get_master_device_parameters first to discover available parameters and ranges.

    Args:
        device_index: Zero-based index of the device in the master track's device chain.
        parameter_index: Zero-based index of the parameter.
        value: New value for the parameter (must be within the parameter's min/max range).
    """
    result = get_connection().send_command("set_master_device_parameter", {
        "device_index": device_index,
        "parameter_index": parameter_index,
        "value": value,
    })
    return json.dumps(result)


def set_return_device_parameter(
    return_index: int, device_index: int, parameter_index: int, value: float
) -> str:
    """Set a parameter value on a device on a return track.

    Use get_return_device_parameters first to discover available parameters and ranges.

    Args:
        return_index: Zero-based index of the return track.
        device_index: Zero-based index of the device in the return track's device chain.
        parameter_index: Zero-based index of the parameter.
        value: New value for the parameter (must be within the parameter's min/max range).
    """
    result = get_connection().send_command("set_return_device_parameter", {
        "return_index": return_index,
        "device_index": device_index,
        "parameter_index": parameter_index,
        "value": value,
    })
    return json.dumps(result)


def set_drum_pad_mute(track_index: int, device_index: int, pad_index: int, mute: bool) -> str:
    """Mute or unmute a specific drum pad in a drum rack.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the drum rack device.
        pad_index: MIDI note number of the drum pad (0-127).
        mute: True to mute the pad, False to unmute.
    """
    result = get_connection().send_command("set_drum_pad_mute", {
        "track_index": track_index,
        "device_index": device_index,
        "pad_index": pad_index,
        "mute": mute,
    })
    return json.dumps(result)


def set_drum_pad_solo(track_index: int, device_index: int, pad_index: int, solo: bool) -> str:
    """Solo or unsolo a specific drum pad in a drum rack.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the drum rack device.
        pad_index: MIDI note number of the drum pad (0-127).
        solo: True to solo the pad, False to unsolo.
    """
    result = get_connection().send_command("set_drum_pad_solo", {
        "track_index": track_index,
        "device_index": device_index,
        "pad_index": pad_index,
        "solo": solo,
    })
    return json.dumps(result)


def delete_master_device(device_index: int) -> str:
    """Delete a device from the master track's device chain.

    Args:
        device_index: Zero-based index of the device to delete.
    """
    result = get_connection().send_command("delete_master_device", {
        "device_index": device_index,
    })
    return json.dumps(result)


def delete_return_device(return_index: int, device_index: int) -> str:
    """Delete a device from a return track's device chain.

    Args:
        return_index: Zero-based index of the return track.
        device_index: Zero-based index of the device to delete.
    """
    result = get_connection().send_command("delete_return_device", {
        "return_index": return_index,
        "device_index": device_index,
    })
    return json.dumps(result)


def move_device(track_index: int, device_index: int, new_index: int) -> str:
    """Move a device to a new position in a track's device chain.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the device to move.
        new_index: Zero-based target position in the device chain.
    """
    result = get_connection().send_command("move_device", {
        "track_index": track_index,
        "device_index": device_index,
        "new_index": new_index,
    })
    return json.dumps(result)


def enable_device(track_index: int, device_index: int, enabled: bool) -> str:
    """Enable or disable a device on a track.

    Args:
        track_index: Zero-based index of the track.
        device_index: Zero-based index of the device.
        enabled: True to enable the device, False to disable it.
    """
    result = get_connection().send_command("enable_device", {
        "track_index": track_index,
        "device_index": device_index,
        "enabled": enabled,
    })
    return json.dumps(result)


TOOLS = [
    get_browser_tree,
    get_browser_items_at_path,
    load_instrument_or_effect,
    load_drum_kit,
    get_device_parameters,
    get_device_display_values,
    set_device_parameter,
    get_master_track_devices,
    get_return_track_devices,
    get_master_device_parameters,
    get_return_device_parameters,
    get_rack_chains,
    set_chain_mixer_value,
    get_drum_chains,
    set_drum_chain_property,
    get_drum_pads,
    delete_device,
    load_device_on_master,
    load_device_on_return,
    set_master_device_parameter,
    set_return_device_parameter,
    set_drum_pad_mute,
    set_drum_pad_solo,
    delete_master_device,
    delete_return_device,
    move_device,
    enable_device,
]
