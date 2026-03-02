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


TOOLS = [
    get_browser_tree,
    get_browser_items_at_path,
    load_instrument_or_effect,
    load_drum_kit,
    get_device_parameters,
    set_device_parameter,
]
