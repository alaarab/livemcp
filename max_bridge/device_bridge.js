autowatch = 1;
inlets = 1;
outlets = 1;

var BRIDGE_SESSION_PREFIX = "livemcp-session-";
var OBJECT_ATTR_ALLOWLIST = {
    "annotation": true,
    "hint": true,
    "text": true,
};
var BOX_ATTR_ALLOWLIST = {
    "background": true,
    "bgcolor": true,
    "border": true,
    "fontface": true,
    "fontname": true,
    "fontsize": true,
    "hidden": true,
    "ignoreclick": true,
    "patching_rect": true,
    "presentation": true,
    "presentation_rect": true,
    "rounded": true,
    "textcolor": true,
    "varname": true,
};
var DISALLOWED_CREATE_CLASSES = {
    "js": true,
    "jsui": true,
    "mxj": true,
    "node.script": true,
    "shell": true,
    "v8": true,
    "v8ui": true,
};
var CAPABILITIES = {
    "selected_device": true,
    "patcher_read": true,
    "patcher_write": true,
    "window_control": true,
    "save": true,
};

var bridgeIds = [];
var nextBridgeId = 1;
var presentationModeState = null;

function bang() {
    initializeBridge();
}

function anything() {
    // The runtime only responds to bridge_request messages from node.script.
}

function bridge_request_json(payloadText) {
    var request;
    var response;

    try {
        request = JSON.parse(String(payloadText || "{}"));
        response = handleRequest(request);
    } catch (err) {
        response = errorEnvelope(
            request && request.id ? request.id : null,
            err.code || "max/bridge-runtime-failure",
            err.message,
            err.details || {}
        );
    }

    outlet(0, "bridge_response_json", JSON.stringify(response));
}

function initializeBridge() {
    refreshBridgeIds();
    if (presentationModeState === null) {
        var openInPresentation = safePatcherAttr("openinpresentation");
        if (openInPresentation !== null && openInPresentation !== undefined) {
            presentationModeState = toInt(openInPresentation) === 1;
        }
    }
}

function handleRequest(request) {
    var command = String(request.command || "");
    var params = request.params || {};
    var requestId = request.id || null;

    initializeBridge();

    if (command === "find_device_session") {
        return okEnvelope(requestId, findDeviceSession(params));
    }
    if (command === "show_editor") {
        return okEnvelope(requestId, showEditor(params));
    }
    if (command === "get_current_patcher") {
        return okEnvelope(requestId, getCurrentPatcher(params));
    }
    if (command === "list_boxes") {
        return okEnvelope(requestId, listBoxesResult(params));
    }
    if (command === "list_named_boxes") {
        return okEnvelope(requestId, listNamedBoxesResult(params));
    }
    if (command === "get_box_attrs") {
        return okEnvelope(requestId, getBoxAttrs(params));
    }
    if (command === "set_box_attrs") {
        return okEnvelope(requestId, setBoxAttrs(params));
    }
    if (command === "create_box") {
        return okEnvelope(requestId, createBox(params));
    }
    if (command === "connect_boxes") {
        return okEnvelope(requestId, connectBoxes(params));
    }
    if (command === "disconnect_boxes") {
        return okEnvelope(requestId, disconnectBoxes(params));
    }
    if (command === "delete_box") {
        return okEnvelope(requestId, deleteBox(params));
    }
    if (command === "set_presentation_rect") {
        return okEnvelope(requestId, setPresentationRect(params));
    }
    if (command === "set_presentation_mode") {
        return okEnvelope(requestId, setPresentationMode(params));
    }
    if (command === "save_device") {
        return okEnvelope(requestId, saveDevice(params));
    }

    return errorEnvelope(
        requestId,
        "max/unknown-command",
        "Unsupported bridge command.",
        { "command": command }
    );
}

function findDeviceSession(params) {
    var info = selectedDeviceInfo();
    var requestedSession = params.bridge_session_id;
    var requestedFingerprint = params.device_fingerprint || null;
    var sessionId;

    if (!info.this_device || !info.this_device.is_m4l) {
        throw bridgeError(
            "max/not-max-device",
            "This device is not running as a Max for Live device.",
            {
                "this_device": info.this_device,
                "selected_device": info.selected_device
            }
        );
    }
    sessionId = bridgeSessionId(info.this_device);
    if (requestedSession && String(requestedSession) !== sessionId) {
        throw bridgeError(
            "max/device-mismatch",
            "bridge_session_id does not match the active selected bridge device.",
            {
                "expected_bridge_session_id": sessionId,
                "received_bridge_session_id": requestedSession
            }
        );
    }
    if (requestedFingerprint && !fingerprintsMatch(info.this_device, requestedFingerprint)) {
        throw bridgeError(
            "max/device-mismatch",
            "Requested device does not match the active bridge device.",
            {
                "expected_device_fingerprint": info.this_device,
                "received_device_fingerprint": requestedFingerprint,
                "selected_device": info.selected_device
            }
        );
    }

    return {
        "bridge_session_id": sessionId,
        "device_fingerprint": info.this_device,
        "capabilities": cloneObject(CAPABILITIES)
    };
}

function showEditor(params) {
    var session = validateActiveSession(params);
    trySelectThisDevice();
    try {
        this.patcher.message("front");
    } catch (_err) {
        // Some patchers rely on wind.visible instead.
    }
    try {
        if (this.patcher.wind) {
            this.patcher.wind.visible = 1;
        }
    } catch (_windErr) {
        // Ignore visibility setter failures.
    }
    return {
        "bridge_session_id": session.bridge_session_id,
        "opened": true,
        "selected_device": session.device_fingerprint
    };
}

function getCurrentPatcher(params) {
    var session = validateActiveSession(params);
    return {
        "bridge_session_id": session.bridge_session_id,
        "selected_device": session.device_fingerprint,
        "name": safeValue(this.patcher.name),
        "filepath": safeValue(this.patcher.filepath),
        "dirty": safeBooleanPatcherAttr("dirty"),
        "locked": safeBooleanPatcherAttr("bglocked"),
        "window_visible": safeWindowVisible(),
        "presentation_mode": presentationModeState === true,
        "box_count": listBoxes().length,
        "patchline_count": listPatchlines().length,
        "capabilities": cloneObject(CAPABILITIES)
    };
}

function listBoxesResult(params) {
    var session = validateActiveSession(params);
    return {
        "bridge_session_id": session.bridge_session_id,
        "boxes": listBoxes()
    };
}

function listNamedBoxesResult(params) {
    var session = validateActiveSession(params);
    return {
        "bridge_session_id": session.bridge_session_id,
        "boxes": listNamedBoxes()
    };
}

function getBoxAttrs(params) {
    var session = validateActiveSession(params);
    var boxId = requireString(params.box_id, "box_id");
    var obj = resolveBox(boxId);
    if (!obj) {
        throw bridgeError("max/box-not-found", "Unknown box id.", { "box_id": boxId });
    }
    return {
        "bridge_session_id": session.bridge_session_id,
        "box_id": ensureBridgeId(obj),
        "object_attrs": collectAttrs(obj, false),
        "box_attrs": collectAttrs(obj, true)
    };
}

function setBoxAttrs(params) {
    var session = validateActiveSession(params);
    var boxId = requireString(params.box_id, "box_id");
    var objectAttrs = params.object_attrs || {};
    var boxAttrs = params.box_attrs || {};
    var obj = resolveBox(boxId);
    var key;

    if (!obj) {
        throw bridgeError("max/box-not-found", "Unknown box id.", { "box_id": boxId });
    }

    for (key in objectAttrs) {
        if (!objectAttrs.hasOwnProperty(key)) {
            continue;
        }
        if (!OBJECT_ATTR_ALLOWLIST[key]) {
            throw bridgeError(
                "max/unsupported-attr",
                "Unsupported object attribute.",
                { "attr": key }
            );
        }
        setObjectAttr(obj, key, objectAttrs[key]);
    }

    for (key in boxAttrs) {
        if (!boxAttrs.hasOwnProperty(key)) {
            continue;
        }
        if (!BOX_ATTR_ALLOWLIST[key]) {
            throw bridgeError(
                "max/unsupported-attr",
                "Unsupported box attribute.",
                { "attr": key }
            );
        }
        validateAttrValue(key, boxAttrs[key]);
        obj.setboxattr(key, boxAttrs[key]);
    }

    markDirty();
    return {
        "bridge_session_id": session.bridge_session_id,
        "box_id": ensureBridgeId(obj),
        "object_attrs": collectAttrs(obj, false),
        "box_attrs": collectAttrs(obj, true)
    };
}

function createBox(params) {
    var session = validateActiveSession(params);
    var classname = requireString(params.classname, "classname");
    var left = requireNumber(params.left, "left");
    var top = requireNumber(params.top, "top");
    var args = params.args || [];
    var objectAttrs = params.object_attrs || {};
    var boxAttrs = params.box_attrs || {};
    var createArgs;
    var obj;

    if (DISALLOWED_CREATE_CLASSES[classname]) {
        throw bridgeError(
            "max/patcher-not-editable",
            "Creating this class is not allowed through the bridge.",
            { "classname": classname }
        );
    }
    if (!(args instanceof Array)) {
        throw bridgeError("max/invalid-params", "args must be an array.", {});
    }

    createArgs = [left, top, classname].concat(args);
    obj = this.patcher.newdefault.apply(this.patcher, createArgs);

    if (boxAttrs.patching_rect) {
        validateAttrValue("patching_rect", boxAttrs.patching_rect);
        obj.setboxattr("patching_rect", boxAttrs.patching_rect);
    }

    if (params.object_attrs || params.box_attrs) {
        setBoxAttrs({
            "bridge_session_id": session.bridge_session_id,
            "box_id": ensureBridgeId(obj),
            "object_attrs": objectAttrs,
            "box_attrs": boxAttrs
        });
    }

    markDirty();
    return {
        "bridge_session_id": session.bridge_session_id,
        "box": boxSummary(obj)
    };
}

function connectBoxes(params) {
    var session = validateActiveSession(params);
    var fromBox = resolveRequiredBox(params.from_box_id);
    var toBox = resolveRequiredBox(params.to_box_id);
    var outlet = requireInt(params.outlet, "outlet");
    var inlet = requireInt(params.inlet, "inlet");
    var hidden = !!params.hidden;

    if (hidden) {
        this.patcher.hiddenconnect(fromBox, outlet, toBox, inlet);
    } else {
        this.patcher.connect(fromBox, outlet, toBox, inlet);
    }

    markDirty();
    return {
        "bridge_session_id": session.bridge_session_id,
        "created": true,
        "patchline": {
            "from_box_id": ensureBridgeId(fromBox),
            "outlet": outlet,
            "to_box_id": ensureBridgeId(toBox),
            "inlet": inlet,
            "hidden": hidden
        }
    };
}

function disconnectBoxes(params) {
    var session = validateActiveSession(params);
    var fromBox = resolveRequiredBox(params.from_box_id);
    var toBox = resolveRequiredBox(params.to_box_id);
    var outlet = requireInt(params.outlet, "outlet");
    var inlet = requireInt(params.inlet, "inlet");

    this.patcher.disconnect(fromBox, outlet, toBox, inlet);
    markDirty();
    return {
        "bridge_session_id": session.bridge_session_id,
        "deleted": true,
        "patchline": {
            "from_box_id": ensureBridgeId(fromBox),
            "outlet": outlet,
            "to_box_id": ensureBridgeId(toBox),
            "inlet": inlet
        }
    };
}

function deleteBox(params) {
    var session = validateActiveSession(params);
    var boxId = requireString(params.box_id, "box_id");
    var obj = resolveBox(boxId);
    if (!obj) {
        throw bridgeError("max/box-not-found", "Unknown box id.", { "box_id": boxId });
    }
    removeStoredBoxId(boxId, obj);
    try {
        this.patcher.remove(obj);
    } catch (_err) {
        try {
            obj.remove();
        } catch (_innerErr) {
            throw bridgeError(
                "max/patcher-not-editable",
                "Could not remove box from patcher.",
                { "box_id": boxId }
            );
        }
    }
    markDirty();
    return {
        "bridge_session_id": session.bridge_session_id,
        "deleted": true,
        "box_id": boxId
    };
}

function setPresentationRect(params) {
    var session = validateActiveSession(params);
    var boxId = requireString(params.box_id, "box_id");
    var presentationRect = params.presentation_rect;
    var obj = resolveBox(boxId);

    if (!obj) {
        throw bridgeError("max/box-not-found", "Unknown box id.", { "box_id": boxId });
    }
    validateAttrValue("presentation_rect", presentationRect);
    obj.setboxattr("presentation", 1);
    obj.setboxattr("presentation_rect", presentationRect);
    markDirty();
    return {
        "bridge_session_id": session.bridge_session_id,
        "box_id": boxId,
        "presentation_rect": normalizeValue(presentationRect)
    };
}

function setPresentationMode(params) {
    var session = validateActiveSession(params);
    var enabled = !!params.enabled;
    var value = enabled ? 1 : 0;

    try {
        this.patcher.message("presentation", value);
    } catch (_err) {
        // Ignore message failures on patchers without an editor window.
    }
    try {
        this.patcher.setattr("openinpresentation", value);
    } catch (_setErr) {
        // Some Max versions do not expose this setter.
    }

    presentationModeState = enabled;
    return {
        "bridge_session_id": session.bridge_session_id,
        "presentation_mode": enabled
    };
}

function saveDevice(params) {
    var session = validateActiveSession(params);
    if (!safeValue(this.patcher.filepath)) {
        throw bridgeError(
            "max/save-requires-path",
            "Device has no current file path and cannot be saved non-interactively.",
            {}
        );
    }
    this.patcher.message("write");
    return {
        "bridge_session_id": session.bridge_session_id,
        "saved": true,
        "filepath": safeValue(this.patcher.filepath)
    };
}

function listBoxes() {
    var boxes = [];
    var obj = this.patcher.firstobject;
    while (obj) {
        boxes.push(boxSummary(obj));
        obj = obj.nextobject;
    }
    return boxes;
}

function listNamedBoxes() {
    var boxes = [];
    var obj = this.patcher.firstobject;
    var varname;
    while (obj) {
        varname = safeBoxAttr(obj, "varname");
        if (varname) {
            boxes.push(boxSummary(obj));
        }
        obj = obj.nextobject;
    }
    return boxes;
}

function listPatchlines() {
    var lines = [];
    var seen = {};
    var obj = this.patcher.firstobject;
    while (obj) {
        collectPatchlinesFromObject(obj, lines, seen);
        obj = obj.nextobject;
    }
    return lines;
}

function boxSummary(obj) {
    return {
        "box_id": ensureBridgeId(obj),
        "maxclass": safeValue(obj.maxclass),
        "varname": safeBoxAttr(obj, "varname"),
        "boxtext": readBoxText(obj),
        "rect": readRect(obj, "patching_rect"),
        "presentation_rect": readRect(obj, "presentation_rect"),
        "hidden": toBoolean(safeBoxAttr(obj, "hidden")),
        "background": toBoolean(safeBoxAttr(obj, "background"))
    };
}

function collectPatchlinesFromObject(obj, lines, seen) {
    var outputs;
    var i;
    var connection;
    var dst;
    var key;
    try {
        outputs = obj.patchcords.outputs || [];
    } catch (_err) {
        outputs = [];
    }
    for (i = 0; i < outputs.length; i++) {
        connection = outputs[i];
        dst = connection.dstobject;
        if (!dst) {
            continue;
        }
        key = [
            ensureBridgeId(obj),
            toInt(connection.outlet),
            ensureBridgeId(dst),
            toInt(connection.inlet)
        ].join(":");
        if (seen[key]) {
            continue;
        }
        seen[key] = true;
        lines.push({
            "from_box_id": ensureBridgeId(obj),
            "outlet": toInt(connection.outlet),
            "to_box_id": ensureBridgeId(dst),
            "inlet": toInt(connection.inlet)
        });
    }
}

function selectedDeviceInfo() {
    var thisDevice = resolveDeviceFingerprint(liveApi("this_device"));
    var selectedDevice = resolveDeviceFingerprint(liveApi("live_set view selected_device"));
    return {
        "this_device": thisDevice,
        "selected_device": selectedDevice,
        "selected_device_is_this_device": fingerprintsMatch(thisDevice, selectedDevice)
    };
}

function resolveDeviceFingerprint(api) {
    var path;
    var trackInfo;
    var className;
    var apiType;
    if (!api || !api.id) {
        return null;
    }
    path = normalizeLivePath(safeValue(api.path));
    trackInfo = parseTrackScope(path);
    className = liveGet(api, "class_name");
    apiType = safeValue(api.type);
    return {
        "device_id": api.id,
        "live_path": path,
        "track_scope": trackInfo.track_scope,
        "track_index": trackInfo.track_index,
        "track_name": trackNameForPath(trackInfo.track_path),
        "device_index": trackInfo.device_index,
        "device_name": liveGet(api, "name"),
        "class_name": className || apiType,
        "device_type": apiType,
        "is_m4l": isM4LDevice(apiType, className)
    };
}

function parseTrackScope(path) {
    var value = String(path || "");
    var match;
    if (!value) {
        return {
            "track_scope": null,
            "track_index": null,
            "track_path": null,
            "device_index": null
        };
    }
    match = value.match(/^live_set tracks (\d+) devices (\d+)$/);
    if (match) {
        return {
            "track_scope": "track",
            "track_index": toInt(match[1]),
            "track_path": "live_set tracks " + match[1],
            "device_index": toInt(match[2])
        };
    }
    match = value.match(/^live_set return_tracks (\d+) devices (\d+)$/);
    if (match) {
        return {
            "track_scope": "return",
            "track_index": toInt(match[1]),
            "track_path": "live_set return_tracks " + match[1],
            "device_index": toInt(match[2])
        };
    }
    match = value.match(/^live_set master_track devices (\d+)$/);
    if (match) {
        return {
            "track_scope": "master",
            "track_index": null,
            "track_path": "live_set master_track",
            "device_index": toInt(match[1])
        };
    }
    return {
        "track_scope": "unknown",
        "track_index": null,
        "track_path": null,
        "device_index": null
    };
}

function trackNameForPath(trackPath) {
    var api;
    if (!trackPath) {
        return null;
    }
    api = liveApi(trackPath);
    return liveGet(api, "name");
}

function isM4LDevice(apiType, className) {
    var typeValue = String(apiType || "");
    var classValue = String(className || "");
    return typeValue === "MaxDevice" || /^MxDevice/.test(typeValue) || /^MxDevice/.test(classValue);
}

function bridgeSessionId(deviceFingerprint) {
    var deviceId = deviceFingerprint && deviceFingerprint.device_id;
    if (deviceId) {
        return BRIDGE_SESSION_PREFIX + deviceId;
    }
    return BRIDGE_SESSION_PREFIX + "unknown";
}

function validateActiveSession(params) {
    return findDeviceSession(params || {});
}

function fingerprintsMatch(left, right) {
    if (!left || !right) {
        return false;
    }
    if (left.device_id && right.device_id) {
        return String(left.device_id) === String(right.device_id);
    }
    if (left.live_path && right.live_path) {
        return String(left.live_path) === String(right.live_path);
    }
    return false;
}

function resolveRequiredBox(boxId) {
    var value = requireString(boxId, "box_id");
    var obj = resolveBox(value);
    if (!obj) {
        throw bridgeError("max/box-not-found", "Unknown box id.", { "box_id": value });
    }
    return obj;
}

function ensureBridgeId(obj) {
    var existing = findStoredIdForObject(obj);
    var varname = safeBoxAttr(obj, "varname");
    if (varname) {
        updateStoredBoxId(obj, existing, varname);
        return varname;
    }
    if (existing) {
        return existing;
    }
    existing = "bridge_anon_" + nextBridgeId;
    nextBridgeId += 1;
    bridgeIds.push({ "id": existing, "obj": obj });
    return existing;
}

function refreshBridgeIds() {
    var obj = this.patcher.firstobject;
    while (obj) {
        ensureBridgeId(obj);
        obj = obj.nextobject;
    }
}

function resolveBox(boxId) {
    var i;
    refreshBridgeIds();
    for (i = 0; i < bridgeIds.length; i++) {
        if (bridgeIds[i].id === boxId) {
            return bridgeIds[i].obj;
        }
    }
    return null;
}

function findStoredIdForObject(obj) {
    var i;
    for (i = 0; i < bridgeIds.length; i++) {
        if (bridgeIds[i].obj === obj) {
            return bridgeIds[i].id;
        }
    }
    return null;
}

function updateStoredBoxId(obj, oldId, newId) {
    var i;
    for (i = 0; i < bridgeIds.length; i++) {
        if (bridgeIds[i].obj === obj || bridgeIds[i].id === oldId) {
            bridgeIds[i].id = newId;
            bridgeIds[i].obj = obj;
            return;
        }
    }
    bridgeIds.push({ "id": newId, "obj": obj });
}

function removeStoredBoxId(boxId, obj) {
    var filtered = [];
    var i;
    for (i = 0; i < bridgeIds.length; i++) {
        if (bridgeIds[i].id === boxId) {
            continue;
        }
        if (obj && bridgeIds[i].obj === obj) {
            continue;
        }
        filtered.push(bridgeIds[i]);
    }
    bridgeIds = filtered;
}

function setObjectAttr(obj, name, value) {
    if (name === "text") {
        try {
            obj.setattr(name, value);
            return;
        } catch (_err) {
            try {
                obj.message("text", value);
                return;
            } catch (_innerErr) {
                throw bridgeError(
                    "max/unsupported-attr",
                    "Could not set object text through the bridge.",
                    { "attr": name }
                );
            }
        }
    }
    try {
        obj.setattr(name, value);
    } catch (_setErr) {
        throw bridgeError(
            "max/unsupported-attr",
            "Could not set object attribute through the bridge.",
            { "attr": name }
        );
    }
}

function collectAttrs(obj, boxAttrs) {
    var getter = boxAttrs ? "getboxattr" : "getattr";
    var nameGetter = boxAttrs ? "getboxattrnames" : "getattrnames";
    var result = {};
    var names;
    var i;
    var value;

    try {
        names = obj[nameGetter]();
    } catch (_err) {
        names = [];
    }

    for (i = 0; i < names.length; i++) {
        try {
            value = normalizeValue(obj[getter](names[i]));
        } catch (_innerErr) {
            continue;
        }
        if (value !== null && value !== undefined) {
            result[names[i]] = value;
        }
    }

    return result;
}

function readBoxText(obj) {
    if (obj.boxtext !== undefined && obj.boxtext !== null) {
        return safeValue(obj.boxtext);
    }
    try {
        return safeValue(obj.getattr("text"));
    } catch (_err) {
        return null;
    }
}

function readRect(obj, attrName) {
    var rect = safeBoxAttr(obj, attrName);
    if (rect === null || rect === undefined) {
        return null;
    }
    return normalizeValue(rect);
}

function safePatcherAttr(name) {
    try {
        return normalizeValue(this.patcher.getattr(name));
    } catch (_err) {
        return null;
    }
}

function safeBooleanPatcherAttr(name) {
    var value = safePatcherAttr(name);
    if (value === null || value === undefined) {
        return false;
    }
    return toBoolean(value);
}

function safeWindowVisible() {
    try {
        if (this.patcher.wind) {
            return toBoolean(this.patcher.wind.visible);
        }
    } catch (_err) {
        // Ignore missing window access.
    }
    return false;
}

function safeBoxAttr(obj, name) {
    try {
        return normalizeValue(obj.getboxattr(name));
    } catch (_err) {
        return null;
    }
}

function normalizeValue(value) {
    var i;
    var copy;
    if (value === undefined || value === null) {
        return null;
    }
    if (typeof value === "number" || typeof value === "string" || typeof value === "boolean") {
        return value;
    }
    if (value instanceof Array) {
        copy = [];
        for (i = 0; i < value.length; i++) {
            copy.push(normalizeValue(value[i]));
        }
        return copy;
    }
    if (typeof value.length === "number") {
        copy = [];
        for (i = 0; i < value.length; i++) {
            copy.push(normalizeValue(value[i]));
        }
        return copy;
    }
    return safeValue(String(value));
}

function normalizeLivePath(value) {
    var text = safeValue(value);
    if (typeof text === "string" && text.length >= 2 && text.charAt(0) === "\"" && text.charAt(text.length - 1) === "\"") {
        return text.substring(1, text.length - 1);
    }
    return text;
}

function cloneObject(source) {
    return JSON.parse(JSON.stringify(source));
}

function safeValue(value) {
    if (value === undefined || value === null) {
        return null;
    }
    return value;
}

function toInt(value) {
    var parsed = parseInt(value, 10);
    if (isNaN(parsed)) {
        return 0;
    }
    return parsed;
}

function toBoolean(value) {
    if (value === true || value === 1 || value === "1") {
        return true;
    }
    return false;
}

function requireString(value, name) {
    if (typeof value !== "string" || value.length === 0) {
        throw bridgeError("max/invalid-params", name + " must be a non-empty string.", {});
    }
    return value;
}

function requireNumber(value, name) {
    var parsed = Number(value);
    if (isNaN(parsed)) {
        throw bridgeError("max/invalid-params", name + " must be numeric.", {});
    }
    return parsed;
}

function requireInt(value, name) {
    var parsed = parseInt(value, 10);
    if (isNaN(parsed)) {
        throw bridgeError("max/invalid-params", name + " must be an integer.", {});
    }
    return parsed;
}

function validateAttrValue(name, value) {
    if (name === "patching_rect" || name === "presentation_rect") {
        if (!(value instanceof Array) || value.length !== 4) {
            throw bridgeError(
                "max/invalid-params",
                name + " must be a four-element array.",
                { "attr": name }
            );
        }
    }
}

function markDirty() {
    try {
        this.patcher.message("dirty");
    } catch (_err) {
        // Ignore patchers that do not expose this message.
    }
}

function liveApi(path) {
    try {
        return new LiveAPI(path);
    } catch (_err) {
        return null;
    }
}

function liveGet(api, propertyName) {
    var raw;
    if (!api) {
        return null;
    }
    try {
        raw = api.get(propertyName);
    } catch (_err) {
        return null;
    }
    if (raw instanceof Array && raw.length > 0) {
        if (raw[0] === propertyName) {
            if (raw.length === 2) {
                return normalizeValue(raw[1]);
            }
            return normalizeValue(raw.slice(1));
        }
        if (raw.length === 1) {
            return normalizeValue(raw[0]);
        }
        return normalizeValue(raw);
    }
    return normalizeValue(raw);
}

function trySelectThisDevice() {
    var thisDevice = liveApi("this_device");
    var liveSetView = liveApi("live_set view");
    if (!thisDevice || !liveSetView || !thisDevice.id) {
        return false;
    }
    try {
        liveSetView.call("select_device", "id " + thisDevice.id);
        return true;
    } catch (_err) {
        return false;
    }
}

function okEnvelope(id, result) {
    return {
        "id": id,
        "status": "success",
        "result": result || {}
    };
}

function errorEnvelope(id, code, message, details) {
    return {
        "id": id,
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details || {}
        }
    };
}

function bridgeError(code, message, details) {
    var err = new Error(message);
    err.code = code;
    err.details = details || {};
    return err;
}
