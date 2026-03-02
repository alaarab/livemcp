"""Device and browser handlers: parameters, browser tree, loading."""

from ..browser import get_browser_tree as _get_browser_tree
from ..browser import get_items_at_path as _get_items_at_path
from ..browser import load_browser_item as _load_browser_item


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


READ_HANDLERS = {
    "get_browser_tree": get_browser_tree,
    "get_browser_items_at_path": get_browser_items_at_path,
    "get_device_parameters": get_device_parameters,
}

WRITE_HANDLERS = {
    "load_browser_item": load_browser_item,
    "load_drum_kit": load_drum_kit,
    "set_device_parameter": set_device_parameter,
}
