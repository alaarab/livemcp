const net = require("net");
const maxApi = require("max-api");

const HOST = "127.0.0.1";
const PORT = 9881;
const BRIDGE_PROTOCOL_VERSION = 1;
const CAPABILITIES = {
  selected_device: true,
  patcher_read: true,
  patcher_write: true,
  window_control: true,
  save: true,
};
const BRIDGE_COMMANDS = {
  get_max_bridge_info: true,
  find_device_session: true,
  show_editor: true,
  get_current_patcher: true,
  list_boxes: true,
  get_box_attrs: true,
  set_box_attrs: true,
  create_box: true,
  connect_boxes: true,
  disconnect_boxes: true,
  delete_box: true,
  set_presentation_rect: true,
  set_presentation_mode: true,
  save_device: true,
};

let server = null;
const pending = new Map();

function success(id, result) {
  return {
    id,
    status: "success",
    result: result || {},
  };
}

function failure(id, code, message, details) {
  return {
    id,
    status: "error",
    error: {
      code,
      message,
      details: details || {},
    },
  };
}

function sendJson(socket, payload) {
  try {
    socket.write(JSON.stringify(payload) + "\n");
  } catch (_err) {
    // Ignore writes to closed sockets.
  }
}

function validateRequest(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return failure(null, "max/invalid-request", "Request must be a JSON object.", {});
  }
  if (payload.id === undefined || payload.id === null) {
    return failure(null, "max/invalid-request", "Request must include an id.", {});
  }
  if (typeof payload.type !== "string" || !payload.type.length) {
    return failure(payload.id, "max/invalid-request", "Request must include a type.", {});
  }
  if (!BRIDGE_COMMANDS[payload.type]) {
    return failure(payload.id, "max/unknown-command", "Unsupported bridge command.", {
      command: payload.type,
    });
  }
  if (payload.params !== undefined && (typeof payload.params !== "object" || Array.isArray(payload.params))) {
    return failure(payload.id, "max/invalid-request", "params must be an object when present.", {});
  }
  return null;
}

async function forwardToRuntime(payload, socket) {
  const requestId = payload.id;
  const pendingKey = String(requestId);
  const timeout = setTimeout(() => {
    const pendingItem = pending.get(pendingKey);
    if (!pendingItem) {
      return;
    }
    sendJson(
      pendingItem.socket,
      failure(
        pendingItem.requestId,
        "max/bridge-timeout",
        "Timed out waiting for Max bridge response.",
        {}
      )
    );
    pending.delete(pendingKey);
  }, 10000);

  pending.set(pendingKey, {
    socket,
    timeout,
    requestId,
  });

  maxApi.outlet("bridge_request_json", JSON.stringify({
    id: requestId,
    command: payload.type,
    params: payload.params || {},
  }));
}

async function handleSocketMessage(line, socket) {
  let payload;
  let validationError;

  if (!line.trim()) {
    return;
  }

  try {
    payload = JSON.parse(line);
  } catch (_err) {
    sendJson(
      socket,
      failure(null, "max/invalid-json", "Could not parse JSON request.", {})
    );
    return;
  }

  validationError = validateRequest(payload);
  if (validationError) {
    sendJson(socket, validationError);
    return;
  }

  if (payload.type === "get_max_bridge_info") {
    sendJson(
      socket,
      success(payload.id, {
        reachable: true,
        protocol_version: BRIDGE_PROTOCOL_VERSION,
        session_mode: "selected-device-server",
        transport: "tcp-json-lines",
        host: HOST,
        port: PORT,
        capabilities: CAPABILITIES,
      })
    );
    return;
  }

  try {
    await forwardToRuntime(payload, socket);
  } catch (err) {
    sendJson(
      socket,
      failure(payload.id, "max/bridge-forward-failed", err.message, {})
    );
  }
}

function attachSocket(socket) {
  let buffer = "";

  socket.setEncoding("utf8");

  socket.on("data", async (chunk) => {
    const parts = (buffer + chunk).split(/\r?\n/);
    buffer = parts.pop();
    for (const line of parts) {
      await handleSocketMessage(line, socket);
    }
  });

  socket.on("close", () => {
    for (const [requestId, pendingItem] of pending.entries()) {
      if (pendingItem.socket === socket) {
        clearTimeout(pendingItem.timeout);
        pending.delete(requestId);
      }
    }
  });
}

function startServer() {
  if (server) {
    return;
  }

  server = net.createServer(attachSocket);
  server.on("error", (err) => {
    maxApi.post("[livemcp.max_bridge] server error: " + err.message);
  });
  server.listen(PORT, HOST, () => {
    maxApi.post("[livemcp.max_bridge] listening on " + HOST + ":" + PORT);
  });
}

function stopServer() {
  if (!server) {
    return;
  }
  server.close();
  server = null;
}

maxApi.addHandler("bridge_response_json", (payloadText) => {
  let payload;
  let key;
  let pendingItem;

  try {
    payload = JSON.parse(String(payloadText || "{}"));
  } catch (err) {
    maxApi.post("[livemcp.max_bridge] invalid response json: " + err.message);
    return;
  }

  key = String(payload.id);
  pendingItem = pending.get(key);

  if (!pendingItem) {
    return;
  }

  clearTimeout(pendingItem.timeout);
  pending.delete(key);

  if (payload.id !== pendingItem.requestId) {
    payload.id = pendingItem.requestId;
  }
  sendJson(pendingItem.socket, payload);
});

maxApi.addHandler("shutdown", () => {
  stopServer();
});

startServer();
