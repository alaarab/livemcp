"""Groove pool tools: list grooves, get/set properties, assign to clips."""

import json

from ..connection import get_connection


def get_groove_pool() -> str:
    """Get all grooves in the groove pool.

    Returns a list of all grooves with their index, name, base subdivision,
    quantization amount, timing amount, random amount, and velocity amount.
    """
    result = get_connection().send_command("get_groove_pool", {})
    return json.dumps(result)


def get_groove_properties(groove_index: int) -> str:
    """Get detailed properties of a specific groove.

    Args:
        groove_index: Zero-based index of the groove in the groove pool.
    """
    result = get_connection().send_command("get_groove_properties", {
        "groove_index": groove_index,
    })
    return json.dumps(result)


def set_groove_property(groove_index: int, property: str, value: float) -> str:
    """Set a property on a groove.

    Args:
        groove_index: Zero-based index of the groove in the groove pool.
        property: Property to set. One of: base, quantization_amount,
            timing_amount, random_amount, velocity_amount.
        value: New value for the property. For base: 0=1/4, 1=1/8, 2=1/8T,
            3=1/16, 4=1/16T, 5=1/32. For amounts: 0.0 to 1.0.
    """
    result = get_connection().send_command("set_groove_property", {
        "groove_index": groove_index,
        "property": property,
        "value": value,
    })
    return json.dumps(result)


def set_clip_groove(track_index: int, clip_index: int, groove_index: int) -> str:
    """Assign a groove from the groove pool to a clip.

    Args:
        track_index: Zero-based index of the track containing the clip.
        clip_index: Zero-based index of the clip slot containing the clip.
        groove_index: Zero-based index of the groove in the groove pool.
    """
    result = get_connection().send_command("set_clip_groove", {
        "track_index": track_index,
        "clip_index": clip_index,
        "groove_index": groove_index,
    })
    return json.dumps(result)


def remove_clip_groove(track_index: int, clip_index: int) -> str:
    """Remove the groove assignment from a clip.

    Note: This tool has a known API limitation — Ableton's API does not support
    removing groove assignments from clips. Consider setting groove properties
    to 0 instead (use set_groove_property to set quantization_amount,
    timing_amount, random_amount, and velocity_amount all to 0.0).

    Args:
        track_index: Zero-based index of the track containing the clip.
        clip_index: Zero-based index of the clip slot containing the clip.
    """
    result = get_connection().send_command("remove_clip_groove", {
        "track_index": track_index,
        "clip_index": clip_index,
    })
    return json.dumps(result)


TOOLS = [
    get_groove_pool,
    get_groove_properties,
    set_groove_property,
    set_clip_groove,
    remove_clip_groove,
]
