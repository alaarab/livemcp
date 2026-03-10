"""Device and browser handlers: parameters, browser tree, loading."""

from ..browser import get_browser_tree as _get_browser_tree
from ..browser import get_items_at_path as _get_items_at_path
from ..browser import load_browser_item as _load_browser_item
from ..browser import find_item_by_uri, navigate_to_item, search_by_name, extract_name_from_uri


def _get_device(song, params):
    """Validate and return a device from track/device indices."""
    track_index = params.get("track_index")
    device_index = params.get("device_index")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if device_index is None:
        raise ValueError("Missing required parameter: device_index")
    track_index = int(track_index)
    device_index = int(device_index)

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]

    if device_index < 0 or device_index >= len(track.devices):
        raise ValueError("Device index {0} out of range (0-{1})".format(
            device_index, len(track.devices) - 1))

    return track, track.devices[device_index]


def _serialize_parameter_value(param):
    """Serialize a device parameter for transport over MCP."""
    result = {
        "name": param.name,
        "value": param.value,
        "min": param.min,
        "max": param.max,
        "is_quantized": param.is_quantized,
    }
    try:
        result["display_value"] = str(param)
    except Exception:
        result["display_value"] = str(param.value)
    return result


def _serialize_chain(chain, chain_index):
    """Serialize a rack or drum chain, including mixer state."""
    mixer = chain.mixer_device
    result = {
        "index": chain_index,
        "name": chain.name,
        "mute": chain.mute,
        "solo": chain.solo,
        "pan": mixer.panning.value,
        "volume": mixer.volume.value,
        "sends": [
            {"index": i, **_serialize_parameter_value(send)}
            for i, send in enumerate(mixer.sends)
        ],
    }
    if hasattr(mixer, "chain_activator"):
        result["chain_activator"] = _serialize_parameter_value(mixer.chain_activator)
    for property_name in ("in_note", "out_note", "choke_group"):
        if hasattr(chain, property_name):
            result[property_name] = getattr(chain, property_name)
    return result


def _get_chain(song, params):
    """Validate and return a chain from track/device/chain indices."""
    track, device = _get_device(song, params)
    if not device.can_have_chains:
        raise ValueError("Device '{0}' does not support chains".format(device.name))

    chain_index = params.get("chain_index")
    if chain_index is None:
        raise ValueError("Missing required parameter: chain_index")
    chain_index = int(chain_index)
    chains = list(device.chains)
    if chain_index < 0 or chain_index >= len(chains):
        raise ValueError("Chain index {0} out of range (0-{1})".format(
            chain_index, len(chains) - 1))
    return track, device, chain_index, chains[chain_index]


def get_browser_tree(control_surface, params):
    """Get hierarchical browser tree. category_type: 'all', 'instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects'."""
    browser = control_surface.application().browser
    category_type = params.get("category_type", "all")
    return _get_browser_tree(browser, category_type)


def get_browser_items_at_path(control_surface, params):
    """Get browser items at a specific path."""
    path = params.get("path")
    if not path:
        raise ValueError("Missing required parameter: path")
    browser = control_surface.application().browser
    log = control_surface.log_message
    return _get_items_at_path(browser, path, log)


def get_device_parameters(control_surface, params):
    """List all parameters of a device."""
    song = control_surface.song()
    track, device = _get_device(song, params)

    parameters = []
    for i, param in enumerate(device.parameters):
        parameters.append({
            "index": i,
            "name": param.name,
            "value": param.value,
            "min": param.min,
            "max": param.max,
            "is_quantized": param.is_quantized,
            "display_value": str(param),
        })

    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "device_name": device.name,
        "parameters": parameters,
    }


def load_browser_item(control_surface, params):
    """Load a browser item onto a track by URI (supports 'uri' or 'item_uri' param key)."""
    track_index = params.get("track_index")
    uri = params.get("uri") or params.get("item_uri")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if not uri:
        raise ValueError("Missing required parameter: uri")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]
    browser = control_surface.application().browser
    return _load_browser_item(control_surface, browser, track, uri)


def load_drum_kit(control_surface, params):
    """Load a drum rack by rack_uri, then load a kit preset by kit_path using the same 3-strategy fallback."""
    track_index = params.get("track_index")
    rack_uri = params.get("rack_uri")
    kit_path = params.get("kit_path")
    if track_index is None:
        raise ValueError("Missing required parameter: track_index")
    if not rack_uri:
        raise ValueError("Missing required parameter: rack_uri")
    if not kit_path:
        raise ValueError("Missing required parameter: kit_path")
    track_index = int(track_index)
    song = control_surface.song()

    if track_index < 0 or track_index >= len(song.tracks):
        raise ValueError("Track index {0} out of range (0-{1})".format(
            track_index, len(song.tracks) - 1))

    track = song.tracks[track_index]
    browser = control_surface.application().browser

    # Load the drum rack first
    _load_browser_item(control_surface, browser, track, rack_uri)

    # Then load the kit preset using the same 3-strategy fallback
    _load_browser_item(control_surface, browser, track, kit_path)

    return {
        "track_index": track_index,
        "rack_uri": rack_uri,
        "kit_path": kit_path,
        "loaded": True,
    }


def set_device_parameter(control_surface, params):
    """Set a device parameter by index or name."""
    song = control_surface.song()
    track, device = _get_device(song, params)

    value = params.get("value")
    if value is None:
        raise ValueError("Missing required parameter: value")
    value = float(value)

    param_index = params.get("parameter_index") or params.get("param_index")
    param_name = params.get("parameter_name") or params.get("param_name")

    if param_index is not None:
        param_index = int(param_index)
        if param_index < 0 or param_index >= len(device.parameters):
            raise ValueError("Parameter index {0} out of range (0-{1})".format(
                param_index, len(device.parameters) - 1))
        param = device.parameters[param_index]
    elif param_name is not None:
        param = None
        for p in device.parameters:
            if p.name == param_name:
                param = p
                break
        if param is None:
            raise ValueError("Parameter not found: {0}".format(param_name))
    else:
        raise ValueError("Must provide either param_index or param_name")

    if value < param.min or value > param.max:
        raise ValueError("Value {0} out of range ({1}-{2})".format(
            value, param.min, param.max))

    param.value = value
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "parameter": param.name,
        "value": value,
    }


def get_master_track_devices(control_surface, params):
    """List devices on the master track."""
    song = control_surface.song()
    devices = []
    for i, device in enumerate(song.master_track.devices):
        devices.append({
            "index": i,
            "name": device.name,
            "class_name": device.class_name,
            "type": int(device.type),
            "is_active": device.is_active,
        })
    return {"devices": devices}


def get_return_track_devices(control_surface, params):
    """List devices on a return track."""
    return_index = params.get("return_index")
    if return_index is None:
        raise ValueError("Missing required parameter: return_index")
    return_index = int(return_index)
    song = control_surface.song()
    if return_index < 0 or return_index >= len(song.return_tracks):
        raise ValueError("Return index {0} out of range (0-{1})".format(
            return_index, len(song.return_tracks) - 1))
    track = song.return_tracks[return_index]
    devices = []
    for i, device in enumerate(track.devices):
        devices.append({
            "index": i,
            "name": device.name,
            "class_name": device.class_name,
            "type": int(device.type),
            "is_active": device.is_active,
        })
    return {"return_index": return_index, "track_name": track.name, "devices": devices}


def get_master_device_parameters(control_surface, params):
    """Get parameters of a device on the master track."""
    device_index = params.get("device_index")
    if device_index is None:
        raise ValueError("Missing required parameter: device_index")
    device_index = int(device_index)
    song = control_surface.song()
    devices = song.master_track.devices
    if device_index < 0 or device_index >= len(devices):
        raise ValueError("Device index {0} out of range (0-{1})".format(
            device_index, len(devices) - 1))
    device = devices[device_index]
    parameters = []
    for i, param in enumerate(device.parameters):
        parameters.append({
            "index": i,
            "name": param.name,
            "value": param.value,
            "min": param.min,
            "max": param.max,
            "is_quantized": param.is_quantized,
            "display_value": str(param),
        })
    return {"device_index": device_index, "device_name": device.name, "parameters": parameters}


def get_return_device_parameters(control_surface, params):
    """Get parameters of a device on a return track."""
    return_index = params.get("return_index")
    device_index = params.get("device_index")
    if return_index is None:
        raise ValueError("Missing required parameter: return_index")
    if device_index is None:
        raise ValueError("Missing required parameter: device_index")
    return_index = int(return_index)
    device_index = int(device_index)
    song = control_surface.song()
    if return_index < 0 or return_index >= len(song.return_tracks):
        raise ValueError("Return index {0} out of range (0-{1})".format(
            return_index, len(song.return_tracks) - 1))
    track = song.return_tracks[return_index]
    if device_index < 0 or device_index >= len(track.devices):
        raise ValueError("Device index {0} out of range (0-{1})".format(
            device_index, len(track.devices) - 1))
    device = track.devices[device_index]
    parameters = []
    for i, param in enumerate(device.parameters):
        parameters.append({
            "index": i,
            "name": param.name,
            "value": param.value,
            "min": param.min,
            "max": param.max,
            "is_quantized": param.is_quantized,
            "display_value": str(param),
        })
    return {
        "return_index": return_index,
        "device_index": device_index,
        "device_name": device.name,
        "parameters": parameters,
    }


def get_device_display_values(control_surface, params):
    """Get all parameters of a device with both raw and display values."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    parameters = []
    for param in device.parameters:
        param_info = {
            "name": param.name,
            "value": param.value,
            "min": param.min,
            "max": param.max,
            "is_enabled": param.is_enabled,
        }
        try:
            param_info["display_value"] = str(param)
        except Exception:
            param_info["display_value"] = str(param.value)
        parameters.append(param_info)
    return {"device_name": device.name, "parameters": parameters}


def get_rack_chains(control_surface, params):
    """List chains inside an instrument or effect rack."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    if not device.can_have_chains:
        raise ValueError("Device '{0}' does not support chains".format(device.name))
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "device_name": device.name,
        "chains": [_serialize_chain(chain, i) for i, chain in enumerate(device.chains)],
    }


def set_chain_mixer_value(control_surface, params):
    """Set a rack chain mixer parameter."""
    song = control_surface.song()
    track, device, chain_index, chain = _get_chain(song, params)
    parameter_name = params.get("parameter_name")
    value = params.get("value")
    if parameter_name is None:
        raise ValueError("Missing required parameter: parameter_name")
    if value is None:
        raise ValueError("Missing required parameter: value")

    normalized = str(parameter_name).strip().lower().replace("-", "_").replace(" ", "_")
    mixer = chain.mixer_device
    if normalized in ("pan", "panning"):
        param = mixer.panning
        target_name = "pan"
    elif normalized == "volume":
        param = mixer.volume
        target_name = "volume"
    elif normalized in ("chain_activator", "activator", "enabled", "on"):
        if not hasattr(mixer, "chain_activator"):
            raise ValueError("Chain activator is not available on this Live version")
        param = mixer.chain_activator
        target_name = "chain_activator"
    elif normalized in ("send", "sends"):
        send_index = params.get("send_index")
        if send_index is None:
            raise ValueError("Missing required parameter: send_index")
        send_index = int(send_index)
        if send_index < 0 or send_index >= len(mixer.sends):
            raise ValueError("Send index {0} out of range (0-{1})".format(
                send_index, len(mixer.sends) - 1))
        param = mixer.sends[send_index]
        target_name = "send"
    else:
        raise ValueError(
            "Unsupported parameter_name '{}'. Expected one of: chain_activator, pan, volume, send".format(
                parameter_name
            )
        )

    value = float(value)
    if value < param.min or value > param.max:
        raise ValueError("Value {0} out of range ({1}-{2})".format(value, param.min, param.max))
    param.value = value

    result = {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "chain_index": chain_index,
        "parameter_name": target_name,
        "value": param.value,
    }
    if target_name == "send":
        result["send_index"] = int(params["send_index"])
    return result


def get_drum_chains(control_surface, params):
    """List drum-chain-specific properties from a drum rack."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    if not device.can_have_drum_pads:
        raise ValueError("Device '{0}' is not a drum rack".format(device.name))
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "device_name": device.name,
        "drum_chains": [_serialize_chain(chain, i) for i, chain in enumerate(device.chains)],
    }


def set_drum_chain_property(control_surface, params):
    """Set a drum-chain-specific property."""
    song = control_surface.song()
    track, device, chain_index, chain = _get_chain(song, params)
    if not device.can_have_drum_pads:
        raise ValueError("Device '{0}' is not a drum rack".format(device.name))

    property_name = params.get("property_name")
    value = params.get("value")
    if property_name is None:
        raise ValueError("Missing required parameter: property_name")
    if value is None:
        raise ValueError("Missing required parameter: value")

    normalized = str(property_name).strip().lower()
    if normalized not in ("in_note", "out_note", "choke_group"):
        raise ValueError(
            "Unsupported property_name '{}'. Expected one of: in_note, out_note, choke_group".format(
                property_name
            )
        )
    if not hasattr(chain, normalized):
        raise ValueError(
            "Property '{}' is not available on this Live version or chain type".format(normalized)
        )

    setattr(chain, normalized, int(value))
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "chain_index": chain_index,
        "property_name": normalized,
        "value": getattr(chain, normalized),
    }


def get_drum_pads(control_surface, params):
    """List drum pads of a drum rack device."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    if not device.can_have_drum_pads:
        raise ValueError("Device '{0}' does not have drum pads".format(device.name))
    pads = []
    pad_list = device.visible_drum_pads if hasattr(device, "visible_drum_pads") else device.drum_pads
    for pad in pad_list:
        pads.append({
            "index": pad.note,
            "name": pad.name,
            "note": pad.note,
            "mute": pad.mute,
            "solo": pad.solo,
        })
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "device_name": device.name,
        "drum_pads": pads,
    }


def delete_device(control_surface, params):
    """Delete a device from a track."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    track_index = int(params["track_index"])
    device_index = int(params["device_index"])
    device_name = device.name
    track.delete_device(device_index)
    return {"track_index": track_index, "device_index": device_index, "deleted_device": device_name}


def _load_device_on_track(control_surface, track, uri):
    """Helper: select track, find browser item by URI, and load it."""
    browser = control_surface.application().browser
    log = control_surface.log_message
    song = control_surface.song()

    item = find_item_by_uri(browser, uri, log)
    if not item:
        log("LiveMCP: URI search failed, trying path navigation for: {0}".format(uri))
        item = navigate_to_item(browser, uri, log)
    if not item:
        log("LiveMCP: Path nav failed, trying name search")
        target = extract_name_from_uri(uri)
        if target and hasattr(browser, "user_library"):
            item = search_by_name(browser.user_library, target, log)
    if not item:
        raise ValueError("Browser item not found: {0}".format(uri))

    song.view.selected_track = track
    browser.load_item(item)
    return {"loaded": True, "item_name": item.name, "track_name": track.name, "uri": uri}


def load_device_on_master(control_surface, params):
    """Load a device onto the master track."""
    uri = params.get("uri")
    if not uri:
        raise ValueError("Missing required parameter: uri")
    song = control_surface.song()
    return _load_device_on_track(control_surface, song.master_track, uri)


def load_device_on_return(control_surface, params):
    """Load a device onto a return track."""
    return_index = params.get("return_index")
    uri = params.get("uri")
    if return_index is None:
        raise ValueError("Missing required parameter: return_index")
    if not uri:
        raise ValueError("Missing required parameter: uri")
    return_index = int(return_index)
    song = control_surface.song()
    if return_index < 0 or return_index >= len(song.return_tracks):
        raise ValueError("Return index {0} out of range (0-{1})".format(
            return_index, len(song.return_tracks) - 1))
    track = song.return_tracks[return_index]
    return _load_device_on_track(control_surface, track, uri)


def set_master_device_parameter(control_surface, params):
    """Set a parameter on a device on the master track."""
    device_index = params.get("device_index")
    parameter_index = params.get("parameter_index")
    value = params.get("value")
    if device_index is None:
        raise ValueError("Missing required parameter: device_index")
    if parameter_index is None:
        raise ValueError("Missing required parameter: parameter_index")
    if value is None:
        raise ValueError("Missing required parameter: value")
    device_index = int(device_index)
    parameter_index = int(parameter_index)
    value = float(value)
    song = control_surface.song()
    devices = song.master_track.devices
    if device_index < 0 or device_index >= len(devices):
        raise ValueError("Device index {0} out of range (0-{1})".format(
            device_index, len(devices) - 1))
    device = devices[device_index]
    if parameter_index < 0 or parameter_index >= len(device.parameters):
        raise ValueError("Parameter index {0} out of range (0-{1})".format(
            parameter_index, len(device.parameters) - 1))
    param = device.parameters[parameter_index]
    if value < param.min or value > param.max:
        raise ValueError("Value {0} out of range ({1}-{2})".format(value, param.min, param.max))
    param.value = value
    return {"device_index": device_index, "parameter": param.name, "value": value}


def set_return_device_parameter(control_surface, params):
    """Set a parameter on a device on a return track."""
    return_index = params.get("return_index")
    device_index = params.get("device_index")
    parameter_index = params.get("parameter_index")
    value = params.get("value")
    if return_index is None:
        raise ValueError("Missing required parameter: return_index")
    if device_index is None:
        raise ValueError("Missing required parameter: device_index")
    if parameter_index is None:
        raise ValueError("Missing required parameter: parameter_index")
    if value is None:
        raise ValueError("Missing required parameter: value")
    return_index = int(return_index)
    device_index = int(device_index)
    parameter_index = int(parameter_index)
    value = float(value)
    song = control_surface.song()
    if return_index < 0 or return_index >= len(song.return_tracks):
        raise ValueError("Return index {0} out of range (0-{1})".format(
            return_index, len(song.return_tracks) - 1))
    track = song.return_tracks[return_index]
    if device_index < 0 or device_index >= len(track.devices):
        raise ValueError("Device index {0} out of range (0-{1})".format(
            device_index, len(track.devices) - 1))
    device = track.devices[device_index]
    if parameter_index < 0 or parameter_index >= len(device.parameters):
        raise ValueError("Parameter index {0} out of range (0-{1})".format(
            parameter_index, len(device.parameters) - 1))
    param = device.parameters[parameter_index]
    if value < param.min or value > param.max:
        raise ValueError("Value {0} out of range ({1}-{2})".format(value, param.min, param.max))
    param.value = value
    return {
        "return_index": return_index,
        "device_index": device_index,
        "parameter": param.name,
        "value": value,
    }


def set_drum_pad_mute(control_surface, params):
    """Mute or unmute a drum pad."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    pad_index = params.get("pad_index")
    mute = params.get("mute")
    if pad_index is None:
        raise ValueError("Missing required parameter: pad_index")
    if mute is None:
        raise ValueError("Missing required parameter: mute")
    pad_index = int(pad_index)
    if not device.can_have_drum_pads:
        raise ValueError("Device '{0}' does not have drum pads".format(device.name))
    device.drum_pads[pad_index].mute = bool(mute)
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "pad_index": pad_index,
        "mute": bool(mute),
    }


def set_drum_pad_solo(control_surface, params):
    """Solo or unsolo a drum pad."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    pad_index = params.get("pad_index")
    solo = params.get("solo")
    if pad_index is None:
        raise ValueError("Missing required parameter: pad_index")
    if solo is None:
        raise ValueError("Missing required parameter: solo")
    pad_index = int(pad_index)
    if not device.can_have_drum_pads:
        raise ValueError("Device '{0}' does not have drum pads".format(device.name))
    device.drum_pads[pad_index].solo = bool(solo)
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "pad_index": pad_index,
        "solo": bool(solo),
    }


def delete_master_device(control_surface, params):
    """Delete a device from the master track."""
    device_index = params.get("device_index")
    if device_index is None:
        raise ValueError("Missing required parameter: device_index")
    device_index = int(device_index)
    song = control_surface.song()
    devices = song.master_track.devices
    if device_index < 0 or device_index >= len(devices):
        raise ValueError("Device index {0} out of range (0-{1})".format(
            device_index, len(devices) - 1))
    device_name = devices[device_index].name
    song.master_track.delete_device(device_index)
    return {"device_index": device_index, "deleted_device": device_name}


def delete_return_device(control_surface, params):
    """Delete a device from a return track."""
    return_index = params.get("return_index")
    device_index = params.get("device_index")
    if return_index is None:
        raise ValueError("Missing required parameter: return_index")
    if device_index is None:
        raise ValueError("Missing required parameter: device_index")
    return_index = int(return_index)
    device_index = int(device_index)
    song = control_surface.song()
    if return_index < 0 or return_index >= len(song.return_tracks):
        raise ValueError("Return index {0} out of range (0-{1})".format(
            return_index, len(song.return_tracks) - 1))
    track = song.return_tracks[return_index]
    if device_index < 0 or device_index >= len(track.devices):
        raise ValueError("Device index {0} out of range (0-{1})".format(
            device_index, len(track.devices) - 1))
    device_name = track.devices[device_index].name
    track.delete_device(device_index)
    return {"return_index": return_index, "device_index": device_index, "deleted_device": device_name}


def move_device(control_surface, params):
    """Move a device to a new position in a track's device chain."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    track_index = int(params["track_index"])
    device_index = int(params["device_index"])
    new_index = params.get("new_index")
    if new_index is None:
        raise ValueError("Missing required parameter: new_index")
    new_index = int(new_index)
    if new_index < 0 or new_index >= len(track.devices):
        raise ValueError("New index {0} out of range (0-{1})".format(
            new_index, len(track.devices) - 1))
    device_name = device.name
    song.move_device(device, track, new_index)
    return {
        "track_index": track_index,
        "device_name": device_name,
        "old_index": device_index,
        "new_index": new_index,
    }


def enable_device(control_surface, params):
    """Enable or disable a device on a track."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    enabled = params.get("enabled")
    if enabled is None:
        raise ValueError("Missing required parameter: enabled")
    enabled = bool(enabled)
    device_name = device.name
    device.is_enabled = enabled
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "device_name": device_name,
        "is_enabled": enabled,
    }


READ_HANDLERS = {
    "get_browser_tree": get_browser_tree,
    "get_browser_items_at_path": get_browser_items_at_path,
    "get_device_parameters": get_device_parameters,
    "get_device_display_values": get_device_display_values,
    "get_master_track_devices": get_master_track_devices,
    "get_return_track_devices": get_return_track_devices,
    "get_master_device_parameters": get_master_device_parameters,
    "get_return_device_parameters": get_return_device_parameters,
    "get_rack_chains": get_rack_chains,
    "get_drum_chains": get_drum_chains,
    "get_drum_pads": get_drum_pads,
}

WRITE_HANDLERS = {
    "load_browser_item": load_browser_item,
    "load_drum_kit": load_drum_kit,
    "set_device_parameter": set_device_parameter,
    "delete_device": delete_device,
    "load_device_on_master": load_device_on_master,
    "load_device_on_return": load_device_on_return,
    "set_master_device_parameter": set_master_device_parameter,
    "set_return_device_parameter": set_return_device_parameter,
    "set_chain_mixer_value": set_chain_mixer_value,
    "set_drum_chain_property": set_drum_chain_property,
    "set_drum_pad_mute": set_drum_pad_mute,
    "set_drum_pad_solo": set_drum_pad_solo,
    "delete_master_device": delete_master_device,
    "delete_return_device": delete_return_device,
    "move_device": move_device,
    "enable_device": enable_device,
}
