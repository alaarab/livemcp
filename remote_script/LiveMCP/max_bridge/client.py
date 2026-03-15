"""Local JSON-lines client for the Max Bridge Hub."""

import json
import socket
import threading

from ..errors import LiveMCPError

HOST = "127.0.0.1"
PORT = 9881
RECV_SIZE = 8192
TIMEOUT = 5.0
MESSAGE_TERMINATOR = b"\n"


class MaxBridgeClient:
    """Short-lived TCP client for the local Max Bridge Hub."""

    def __init__(self, host=HOST, port=PORT, timeout=TIMEOUT):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._request_id = 0
        self._request_id_lock = threading.Lock()

    def _next_request_id(self):
        with self._request_id_lock:
            self._request_id += 1
            return self._request_id

    def _open_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._timeout)
        sock.connect((self._host, self._port))
        return sock

    @staticmethod
    def _error_from_payload(payload):
        if isinstance(payload, dict):
            return LiveMCPError(
                payload.get("code") or "max/bridge-error",
                str(payload.get("message") or "Unknown Max bridge error"),
                payload.get("details"),
            )
        return LiveMCPError("max/bridge-error", str(payload or "Unknown Max bridge error"))

    @staticmethod
    def _ids_match(expected_id, response_id):
        if response_id is None:
            return True
        return str(response_id) == str(expected_id)

    def send_command(self, command_type, params=None):
        """Send a command to the Max bridge and return the decoded result."""
        if params is None:
            params = {}

        request_id = self._next_request_id()
        payload = json.dumps(
            {"id": request_id, "type": command_type, "params": params}
        ).encode("utf-8") + MESSAGE_TERMINATOR

        try:
            with self._open_socket() as sock:
                sock.sendall(payload)
                buffer = b""
                while MESSAGE_TERMINATOR not in buffer:
                    chunk = sock.recv(RECV_SIZE)
                    if not chunk:
                        raise LiveMCPError(
                            "max/bridge-unavailable",
                            "Max bridge closed the connection unexpectedly.",
                        )
                    buffer += chunk
        except LiveMCPError:
            raise
        except (OSError, socket.timeout) as exc:
            raise LiveMCPError(
                "max/bridge-unavailable",
                "Max bridge is not currently reachable.",
                {"host": self._host, "port": self._port, "error": str(exc)},
            )

        message, _, _ = buffer.partition(MESSAGE_TERMINATOR)
        if not message:
            raise LiveMCPError("max/protocol-error", "Max bridge returned an empty response.")

        try:
            response = json.loads(message.decode("utf-8"))
        except (json.JSONDecodeError, ValueError) as exc:
            raise LiveMCPError(
                "max/protocol-error",
                "Max bridge returned invalid JSON.",
                {"error": str(exc)},
            )

        response_id = response.get("id")
        if not self._ids_match(request_id, response_id):
            raise LiveMCPError(
                "max/protocol-error",
                "Mismatched Max bridge response id.",
                {"expected_id": request_id, "response_id": response_id},
            )

        if response.get("status") == "error":
            raise self._error_from_payload(response.get("error") or response.get("message"))

        return response.get("result", {})

    def get_info(self):
        """Return bridge capability metadata or a structured unavailable payload."""
        try:
            result = self.send_command("get_max_bridge_info", {})
            result.setdefault("reachable", True)
            result.setdefault("transport", "tcp-json-lines")
            result.setdefault("host", self._host)
            result.setdefault("port", self._port)
            return result
        except LiveMCPError as exc:
            return {
                "reachable": False,
                "transport": "tcp-json-lines",
                "host": self._host,
                "port": self._port,
                "error_code": exc.code,
                "error_message": str(exc),
                "capabilities": {
                    "selected_device": False,
                    "patcher_read": False,
                    "patcher_write": False,
                    "window_control": False,
                    "save": False,
                },
            }
