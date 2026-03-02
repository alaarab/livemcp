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

_lock = threading.Lock()
_instance = None


class AbletonConnection:
    """Manages a persistent TCP connection to the LiveMCP remote script."""

    def __init__(self):
        self._socket = None

    def connect(self):
        """Establish connection and validate with a get_session_info ping."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(TIMEOUT)
        self._socket.connect((HOST, PORT))
        # Validate the connection
        self.send_command("get_session_info", {})

    def disconnect(self):
        """Close the socket connection."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def send_command(self, command_type: str, params: dict) -> dict:
        """Send a JSON command and return the parsed result.

        Raises RuntimeError if the remote script returns an error status.
        Raises ConnectionError after exhausting retries.
        """
        payload = json.dumps({"type": command_type, "params": params}).encode("utf-8")

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                if self._socket is None:
                    self.connect()
                    # If this is a retry reconnect, don't re-validate (connect already did)
                    if attempt > 0:
                        pass

                self._socket.sendall(payload)

                # Chunked receive with JSON boundary detection
                buffer = b""
                self._socket.settimeout(TIMEOUT)
                while True:
                    chunk = self._socket.recv(RECV_SIZE)
                    if not chunk:
                        raise ConnectionError("Remote script closed the connection")
                    buffer += chunk
                    try:
                        response = json.loads(buffer.decode("utf-8"))
                        break
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

                if response.get("status") == "error":
                    error_msg = response.get("error") or response.get("message", "Unknown error")
                    raise RuntimeError(error_msg)

                return response.get("result", {})

            except (ConnectionError, OSError, socket.timeout) as e:
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
