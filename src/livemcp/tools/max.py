"""Max for Live tools: selected-device inspection and native patcher bridge control."""

import json
from typing import Any, Optional

from typing_extensions import TypedDict

from ..connection import get_connection


class MaxBridgeStatusInfo(TypedDict, total=False):
    reachable: bool
    protocol_version: int
    session_mode: str
    transport: str
    host: str
    port: int
    error_code: str
    error_message: str
    capabilities: dict[str, bool]


class MaxDeviceState(TypedDict, total=False):
    track_scope: str
    track_index: Optional[int]
    track_name: Optional[str]
    device_index: Optional[int]
    device_name: Optional[str]
    class_name: Optional[str]
    type: Optional[int]
    is_active: Optional[bool]
    live_path: Optional[str]


class SelectedMaxDeviceInfo(TypedDict, total=False):
    track: dict[str, Any]
    selected_device: Optional[MaxDeviceState]
    supported: bool
    unsupported_reason: Optional[str]
    bridge_attached: bool
    bridge_session_id: Optional[str]
    bridge_capabilities: dict[str, bool]
    max_bridge: MaxBridgeStatusInfo


class CurrentPatcherInfo(TypedDict, total=False):
    bridge_session_id: str
    selected_device: MaxDeviceState
    name: str
    filepath: str
    dirty: bool
    locked: bool
    window_visible: bool
    presentation_mode: bool
    box_count: int
    patchline_count: int
    capabilities: dict[str, bool]


class PatcherBoxInfo(TypedDict, total=False):
    box_id: str
    maxclass: str
    varname: str
    boxtext: str
    rect: list[float]
    presentation_rect: list[float]
    hidden: bool
    background: bool


class PatcherBoxesInfo(TypedDict, total=False):
    bridge_session_id: str
    boxes: list[PatcherBoxInfo]
    total_box_count: int
    complete: bool
    enumeration_mode: str
    fallback_reason: str


class BoxAttrsInfo(TypedDict, total=False):
    bridge_session_id: str
    box_id: str
    object_attrs: dict[str, Any]
    box_attrs: dict[str, Any]


def _bridge_params(bridge_session_id: Optional[str]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if bridge_session_id is not None:
        params["bridge_session_id"] = bridge_session_id
    return params


def get_selected_max_device() -> SelectedMaxDeviceInfo:
    """Return the selected Live device when it is a Max for Live device.

    Returns selection metadata, whether the selected device is supported,
    the active bridge session id when attached, and Max bridge capability state.
    """
    result = get_connection().send_command("get_selected_max_device", {})
    return result


def open_selected_device_in_max(bridge_session_id: Optional[str] = None) -> str:
    """Open the selected Max device in the native Max editor."""
    result = get_connection().send_command(
        "open_selected_device_in_max",
        _bridge_params(bridge_session_id),
    )
    return json.dumps(result)


def get_current_patcher(bridge_session_id: Optional[str] = None) -> CurrentPatcherInfo:
    """Return summary metadata for the currently attached patcher."""
    result = get_connection().send_command("get_current_patcher", _bridge_params(bridge_session_id))
    return result


def list_patcher_boxes(
    bridge_session_id: Optional[str] = None,
    named_only: bool = False,
) -> PatcherBoxesInfo:
    """List boxes in the attached patcher.

    When `named_only=True`, request only boxes with a stable Max `varname`.
    The Ableton-side bridge may also automatically fall back to this smaller
    response when full enumeration times out on larger patchers.
    """
    params = _bridge_params(bridge_session_id)
    if named_only:
        params["named_only"] = True
    result = get_connection().send_command("list_patcher_boxes", params)
    return result


def get_box_attrs(box_id: str, bridge_session_id: Optional[str] = None) -> BoxAttrsInfo:
    """Get object attrs and box attrs for a patcher box."""
    params = _bridge_params(bridge_session_id)
    params["box_id"] = box_id
    result = get_connection().send_command("get_box_attrs", params)
    return result


def set_box_attrs(
    box_id: str,
    object_attrs: Optional[dict[str, Any]] = None,
    box_attrs: Optional[dict[str, Any]] = None,
    bridge_session_id: Optional[str] = None,
) -> str:
    """Set allowlisted attrs for a patcher box."""
    params = _bridge_params(bridge_session_id)
    params["box_id"] = box_id
    if object_attrs is not None:
        params["object_attrs"] = object_attrs
    if box_attrs is not None:
        params["box_attrs"] = box_attrs
    result = get_connection().send_command("set_box_attrs", params)
    return json.dumps(result)


def create_box(
    classname: str,
    left: float,
    top: float,
    args: Optional[list[Any]] = None,
    object_attrs: Optional[dict[str, Any]] = None,
    box_attrs: Optional[dict[str, Any]] = None,
    bridge_session_id: Optional[str] = None,
) -> str:
    """Create a new Max object box in the attached patcher."""
    params = _bridge_params(bridge_session_id)
    params.update(
        {
            "classname": classname,
            "left": left,
            "top": top,
        }
    )
    if args is not None:
        params["args"] = args
    if object_attrs is not None:
        params["object_attrs"] = object_attrs
    if box_attrs is not None:
        params["box_attrs"] = box_attrs
    result = get_connection().send_command("create_box", params)
    return json.dumps(result)


def create_patchline(
    from_box_id: str,
    outlet: int,
    to_box_id: str,
    inlet: int,
    hidden: bool = False,
    bridge_session_id: Optional[str] = None,
) -> str:
    """Create a patchline between two boxes."""
    params = _bridge_params(bridge_session_id)
    params.update(
        {
            "from_box_id": from_box_id,
            "outlet": outlet,
            "to_box_id": to_box_id,
            "inlet": inlet,
            "hidden": hidden,
        }
    )
    result = get_connection().send_command("create_patchline", params)
    return json.dumps(result)


def delete_box(box_id: str, bridge_session_id: Optional[str] = None) -> str:
    """Delete a box from the attached patcher."""
    params = _bridge_params(bridge_session_id)
    params["box_id"] = box_id
    result = get_connection().send_command("delete_box", params)
    return json.dumps(result)


def delete_patchline(
    from_box_id: str,
    outlet: int,
    to_box_id: str,
    inlet: int,
    bridge_session_id: Optional[str] = None,
) -> str:
    """Delete a patchline between two boxes."""
    params = _bridge_params(bridge_session_id)
    params.update(
        {
            "from_box_id": from_box_id,
            "outlet": outlet,
            "to_box_id": to_box_id,
            "inlet": inlet,
        }
    )
    result = get_connection().send_command("delete_patchline", params)
    return json.dumps(result)


def set_presentation_rect(
    box_id: str,
    presentation_rect: list[float],
    bridge_session_id: Optional[str] = None,
) -> str:
    """Set presentation rect for a patcher box."""
    params = _bridge_params(bridge_session_id)
    params["box_id"] = box_id
    params["presentation_rect"] = presentation_rect
    result = get_connection().send_command("set_presentation_rect", params)
    return json.dumps(result)


def toggle_presentation_mode(
    enabled: Optional[bool] = None,
    bridge_session_id: Optional[str] = None,
) -> str:
    """Toggle or set the attached patcher's presentation mode."""
    params = _bridge_params(bridge_session_id)
    if enabled is not None:
        params["enabled"] = enabled
    result = get_connection().send_command("toggle_presentation_mode", params)
    return json.dumps(result)


def save_max_device(bridge_session_id: Optional[str] = None) -> str:
    """Save the selected Max device to its existing file path."""
    result = get_connection().send_command("save_max_device", _bridge_params(bridge_session_id))
    return json.dumps(result)


TOOLS = [
    get_selected_max_device,
    open_selected_device_in_max,
    get_current_patcher,
    list_patcher_boxes,
    get_box_attrs,
    set_box_attrs,
    create_box,
    create_patchline,
    delete_box,
    delete_patchline,
    set_presentation_rect,
    toggle_presentation_mode,
    save_max_device,
]
