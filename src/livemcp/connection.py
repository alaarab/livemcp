"""TCP socket connection to the LiveMCP remote script running inside Ableton Live."""

import json
import socket
import time
import threading

HOST = "127.0.0.1"
PORT = 9877
RECV_SIZE = 8192
TIMEOUT = 15.0
MAX_RETRIES = 3
RETRY_DELAY = 1.0
MESSAGE_TERMINATOR = b"\n"

_lock = threading.Lock()
_instance = None


class AbletonConnection:
    """Manages a persistent TCP connection to the LiveMCP remote script."""

    def __init__(self):
        self._socket = None
        self._recv_buffer = b""
        self._request_lock = threading.RLock()
        self._request_id_lock = threading.Lock()
        self._request_id = 0

    def _next_request_id(self) -> int:
        """Return the next monotonically increasing request id."""
        with self._request_id_lock:
            self._request_id += 1
            return self._request_id

    @staticmethod
    def _build_payload(command_type: str, params: dict, request_id: int) -> bytes:
        """Encode a framed command payload."""
        return json.dumps({"id": request_id, "type": command_type, "params": params}).encode("utf-8")

    def _open_socket(self):
        """Create and connect a fresh TCP socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((HOST, PORT))
        return sock

    def _send_payload_unlocked(self, payload: bytes, expected_request_id: int) -> dict:
        """Send a framed payload and return the decoded response."""
        self._socket.sendall(payload + MESSAGE_TERMINATOR)
        self._socket.settimeout(TIMEOUT)

        while MESSAGE_TERMINATOR not in self._recv_buffer:
            chunk = self._socket.recv(RECV_SIZE)
            if not chunk:
                raise ConnectionError("Remote script closed the connection")
            self._recv_buffer += chunk

        message, _, self._recv_buffer = self._recv_buffer.partition(MESSAGE_TERMINATOR)
        if not message:
            raise ConnectionError("Remote script returned an empty response")
        response = json.loads(message.decode("utf-8"))
        response_id = response.get("id")
        if response_id is not None and response_id != expected_request_id:
            raise ConnectionError(
                "Mismatched response id: expected {0}, got {1}".format(
                    expected_request_id,
                    response_id,
                )
            )
        return response

    def connect(self):
        """Establish connection and validate with a get_session_info ping."""
        self.disconnect()
        self._socket = self._open_socket()
        self._recv_buffer = b""
        request_id = self._next_request_id()
        payload = self._build_payload("get_session_info", {}, request_id)
        response = self._send_payload_unlocked(payload, expected_request_id=request_id)
        if response.get("status") == "error":
            error_msg = response.get("error") or response.get("message", "Unknown error")
            raise RuntimeError(error_msg)

    def disconnect(self):
        """Close the socket connection."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self._recv_buffer = b""

    def send_command(self, command_type: str, params: dict) -> dict:
        """Send a JSON command and return the parsed result.

        Raises RuntimeError if the remote script returns an error status.
        Raises ConnectionError after exhausting retries.
        """
        request_id = self._next_request_id()
        payload = self._build_payload(command_type, params, request_id)

        with self._request_lock:
            last_error = None
            for attempt in range(MAX_RETRIES):
                try:
                    if self._socket is None:
                        self.connect()

                    response = self._send_payload_unlocked(payload, expected_request_id=request_id)
                    if response.get("status") == "error":
                        error_msg = response.get("error") or response.get("message", "Unknown error")
                        raise RuntimeError(error_msg)

                    return response.get("result", {})

                except (ConnectionError, OSError, socket.timeout, json.JSONDecodeError) as e:
                    last_error = e
                    self.disconnect()
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)

            raise ConnectionError(
                "Failed to communicate with Ableton after {0} attempts: {1}".format(
                    MAX_RETRIES, last_error
                )
            )


def get_connection() -> AbletonConnection:
    """Return a global singleton AbletonConnection, creating it on first use."""
    global _instance
    with _lock:
        if _instance is None:
            _instance = AbletonConnection()
        return _instance
