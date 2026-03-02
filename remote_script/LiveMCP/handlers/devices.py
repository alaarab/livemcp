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


def get_browser_tree(control_surface, params):
    """Get hierarchical browser tree."""
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
    """Load a browser item onto a track."""
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
    """Load a drum rack and then load a drum kit into it."""
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

    # Then load the kit via path navigation
    log = control_surface.log_message
    result = _get_items_at_path(browser, kit_path, log)
    if "error" in result:
        raise ValueError("Kit path error: {0}".format(result["error"]))

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


def get_rack_chains(control_surface, params):
    """List chains inside an instrument or effect rack."""
    song = control_surface.song()
    track, device = _get_device(song, params)
    if not device.can_have_chains:
        raise ValueError("Device '{0}' does not support chains".format(device.name))
    chains = []
    for i, chain in enumerate(device.chains):
        chains.append({
            "index": i,
            "name": chain.name,
            "mute": chain.mute,
            "solo": chain.solo,
            "volume": chain.mixer_device.volume.value,
        })
    return {
        "track_index": int(params["track_index"]),
        "device_index": int(params["device_index"]),
        "device_name": device.name,
        "chains": chains,
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
    device_name = track.devices[device_index].name
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


READ_HANDLERS = {
    "get_browser_tree": get_browser_tree,
    "get_browser_items_at_path": get_browser_items_at_path,
    "get_device_parameters": get_device_parameters,
    "get_master_track_devices": get_master_track_devices,
    "get_return_track_devices": get_return_track_devices,
    "get_master_device_parameters": get_master_device_parameters,
    "get_return_device_parameters": get_return_device_parameters,
    "get_rack_chains": get_rack_chains,
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
    "set_drum_pad_mute": set_drum_pad_mute,
    "set_drum_pad_solo": set_drum_pad_solo,
}
