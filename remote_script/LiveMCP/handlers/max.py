"""Max for Live bridge handlers."""

from ..errors import LiveMCPError
from .session import _describe_device, _describe_track_location, _get_selected_device_on_track


def _max_bridge_info(control_surface):
    server = getattr(control_surface, "_server", None)
    if server is None:
        return {
            "reachable": False,
            "capabilities": {
                "selected_device": False,
                "patcher_read": False,
                "patcher_write": False,
                "window_control": False,
                "save": False,
            },
            "error_code": "max/bridge-unavailable",
            "error_message": "LiveMCP Max bridge is not initialized.",
        }
    return server.get_max_bridge_info()


def _max_bridge_client(control_surface):
    server = getattr(control_surface, "_server", None)
    if server is None:
        raise LiveMCPError("max/bridge-unavailable", "LiveMCP Max bridge is not initialized.")
    return server.get_max_bridge_client()


def _build_live_path(track_info, device_index):
    scope = track_info.get("scope")
    track_index = track_info.get("index")
    if scope == "track" and track_index is not None:
        return "live_set tracks {0} devices {1}".format(track_index, device_index)
    if scope == "return" and track_index is not None:
        return "live_set return_tracks {0} devices {1}".format(track_index, device_index)
    if scope == "master":
        return "live_set master_track devices {0}".format(device_index)
    return None


def _is_max_device(device):
    class_name = getattr(device, "class_name", None)
    if class_name == "MaxDevice":
        return True
    return str(class_name or "").startswith("MxDevice")


def _selected_device_context(control_surface):
    song = control_surface.song()
    track = song.view.selected_track
    track_info = _describe_track_location(song, track)
    if track is None:
        return {
            "track": track_info,
            "selected_device": None,
            "supported": False,
            "unsupported_reason": "No track is currently selected.",
            "bridge_attached": False,
            "bridge_session_id": None,
            "bridge_capabilities": {},
            "max_bridge": _max_bridge_info(control_surface),
        }

    device = _get_selected_device_on_track(track)
    if device is None:
        return {
            "track": track_info,
            "selected_device": None,
            "supported": False,
            "unsupported_reason": "No device is currently selected.",
            "bridge_attached": False,
            "bridge_session_id": None,
            "bridge_capabilities": {},
            "max_bridge": _max_bridge_info(control_surface),
        }

    device_info = _describe_device(song, track, device)
    device_info["live_path"] = _build_live_path(track_info, device_info.get("device_index"))

    result = {
        "track": track_info,
        "selected_device": device_info,
        "supported": False,
        "unsupported_reason": None,
        "bridge_attached": False,
        "bridge_session_id": None,
        "bridge_capabilities": {},
        "max_bridge": _max_bridge_info(control_surface),
    }

    if not _is_max_device(device):
        result["unsupported_reason"] = "Selected device is not a Max for Live device."
        return result

    result["supported"] = True
    return result


def _resolve_bridge_session(control_surface, params):
    context = _selected_device_context(control_surface)
    if context["selected_device"] is None:
        raise LiveMCPError("max/no-device-selected", context["unsupported_reason"])
    if not context["supported"]:
        raise LiveMCPError(
            "max/not-max-device",
            context["unsupported_reason"],
            {"selected_device": context["selected_device"]},
        )

    bridge_info = context["max_bridge"]
    if not bridge_info.get("reachable"):
        raise LiveMCPError(
            bridge_info.get("error_code") or "max/bridge-unavailable",
            bridge_info.get("error_message") or "Max bridge is not currently reachable.",
            {"selected_device": context["selected_device"]},
        )

    bridge_client = _max_bridge_client(control_surface)
    request = {
        "device_fingerprint": context["selected_device"],
    }
    bridge_session_id = params.get("bridge_session_id")
    if bridge_session_id:
        request["bridge_session_id"] = bridge_session_id

    session_info = bridge_client.send_command("find_device_session", request)
    context["bridge_attached"] = True
    context["bridge_session_id"] = session_info.get("bridge_session_id")
    context["bridge_capabilities"] = session_info.get("capabilities", {})
    return context, bridge_client, session_info


def get_selected_max_device(control_surface, params):
    """Describe the currently selected Max device and bridge attachment state."""
    context = _selected_device_context(control_surface)

    if context["supported"] and context["max_bridge"].get("reachable"):
        try:
            bridge_client = _max_bridge_client(control_surface)
            session_info = bridge_client.send_command(
                "find_device_session",
                {"device_fingerprint": context["selected_device"]},
            )
            context["bridge_attached"] = True
            context["bridge_session_id"] = session_info.get("bridge_session_id")
            context["bridge_capabilities"] = session_info.get("capabilities", {})
        except LiveMCPError as exc:
            context["bridge_attached"] = False
            context["bridge_capabilities"] = {}
            if context["unsupported_reason"] is None:
                context["unsupported_reason"] = str(exc)

    return context


def open_selected_device_in_max(control_surface, params):
    """Open the selected device's attached Max patcher window."""
    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    result = bridge_client.send_command(
        "show_editor",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
        },
    )
    result.setdefault("bridge_session_id", session_info.get("bridge_session_id"))
    return result


def get_current_patcher(control_surface, params):
    """Return summary metadata for the attached patcher session."""
    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    result = bridge_client.send_command(
        "get_current_patcher",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
        },
    )
    result.setdefault("bridge_session_id", session_info.get("bridge_session_id"))
    result.setdefault("selected_device", context["selected_device"])
    return result


def list_patcher_boxes(control_surface, params):
    """List all boxes in the attached patcher."""
    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    result = bridge_client.send_command(
        "list_boxes",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
        },
    )
    result.setdefault("bridge_session_id", session_info.get("bridge_session_id"))
    return result


def get_box_attrs(control_surface, params):
    """Return object and box attrs for a patcher box."""
    box_id = params.get("box_id")
    if not box_id:
        raise LiveMCPError("max/box-not-found", "Missing required parameter: box_id")

    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    result = bridge_client.send_command(
        "get_box_attrs",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
            "box_id": box_id,
        },
    )
    result.setdefault("bridge_session_id", session_info.get("bridge_session_id"))
    return result


def set_box_attrs(control_surface, params):
    """Set allowlisted object and box attrs for a patcher box."""
    box_id = params.get("box_id")
    if not box_id:
        raise LiveMCPError("max/box-not-found", "Missing required parameter: box_id")

    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    return bridge_client.send_command(
        "set_box_attrs",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
            "box_id": box_id,
            "object_attrs": params.get("object_attrs", {}),
            "box_attrs": params.get("box_attrs", {}),
        },
    )


def create_box(control_surface, params):
    """Create a new Max object box in the attached patcher."""
    classname = params.get("classname")
    left = params.get("left")
    top = params.get("top")
    if not classname:
        raise LiveMCPError("max/invalid-params", "Missing required parameter: classname")
    if left is None or top is None:
        raise LiveMCPError("max/invalid-params", "Missing required parameters: left and top")

    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    return bridge_client.send_command(
        "create_box",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
            "classname": classname,
            "left": float(left),
            "top": float(top),
            "args": params.get("args", []),
            "object_attrs": params.get("object_attrs", {}),
            "box_attrs": params.get("box_attrs", {}),
        },
    )


def create_patchline(control_surface, params):
    """Connect two boxes in the attached patcher."""
    from_box_id = params.get("from_box_id")
    to_box_id = params.get("to_box_id")
    outlet = params.get("outlet")
    inlet = params.get("inlet")
    if not from_box_id or not to_box_id:
        raise LiveMCPError(
            "max/patchline-not-found",
            "Missing required parameters: from_box_id and to_box_id",
        )
    if outlet is None or inlet is None:
        raise LiveMCPError("max/invalid-params", "Missing required parameters: outlet and inlet")

    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    return bridge_client.send_command(
        "connect_boxes",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
            "from_box_id": from_box_id,
            "to_box_id": to_box_id,
            "outlet": int(outlet),
            "inlet": int(inlet),
            "hidden": bool(params.get("hidden", False)),
        },
    )


def delete_box(control_surface, params):
    """Delete a box from the attached patcher."""
    box_id = params.get("box_id")
    if not box_id:
        raise LiveMCPError("max/box-not-found", "Missing required parameter: box_id")

    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    return bridge_client.send_command(
        "delete_box",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
            "box_id": box_id,
        },
    )


def delete_patchline(control_surface, params):
    """Disconnect two boxes in the attached patcher."""
    from_box_id = params.get("from_box_id")
    to_box_id = params.get("to_box_id")
    outlet = params.get("outlet")
    inlet = params.get("inlet")
    if not from_box_id or not to_box_id:
        raise LiveMCPError(
            "max/patchline-not-found",
            "Missing required parameters: from_box_id and to_box_id",
        )
    if outlet is None or inlet is None:
        raise LiveMCPError("max/invalid-params", "Missing required parameters: outlet and inlet")

    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    return bridge_client.send_command(
        "disconnect_boxes",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
            "from_box_id": from_box_id,
            "to_box_id": to_box_id,
            "outlet": int(outlet),
            "inlet": int(inlet),
        },
    )


def set_presentation_rect(control_surface, params):
    """Set a box's presentation rect and ensure it belongs to presentation."""
    box_id = params.get("box_id")
    presentation_rect = params.get("presentation_rect")
    if not box_id:
        raise LiveMCPError("max/box-not-found", "Missing required parameter: box_id")
    if presentation_rect is None:
        raise LiveMCPError(
            "max/invalid-params",
            "Missing required parameter: presentation_rect",
        )

    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    return bridge_client.send_command(
        "set_presentation_rect",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
            "box_id": box_id,
            "presentation_rect": presentation_rect,
        },
    )


def toggle_presentation_mode(control_surface, params):
    """Toggle or set the attached patcher's presentation mode."""
    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    request = {
        "bridge_session_id": session_info.get("bridge_session_id"),
        "device_fingerprint": context["selected_device"],
    }
    if "enabled" in params:
        request["enabled"] = bool(params.get("enabled"))
    return bridge_client.send_command("set_presentation_mode", request)


def save_max_device(control_surface, params):
    """Save the attached Max device in place."""
    context, bridge_client, session_info = _resolve_bridge_session(control_surface, params)
    return bridge_client.send_command(
        "save_device",
        {
            "bridge_session_id": session_info.get("bridge_session_id"),
            "device_fingerprint": context["selected_device"],
        },
    )


READ_HANDLERS = {
    "get_selected_max_device": get_selected_max_device,
    "get_current_patcher": get_current_patcher,
    "list_patcher_boxes": list_patcher_boxes,
    "get_box_attrs": get_box_attrs,
    "open_selected_device_in_max": open_selected_device_in_max,
    "set_box_attrs": set_box_attrs,
    "create_box": create_box,
    "create_patchline": create_patchline,
    "delete_box": delete_box,
    "delete_patchline": delete_patchline,
    "set_presentation_rect": set_presentation_rect,
    "toggle_presentation_mode": toggle_presentation_mode,
    "save_max_device": save_max_device,
}

WRITE_HANDLERS = {}
