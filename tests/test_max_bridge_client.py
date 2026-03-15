import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from remote_script.LiveMCP.max_bridge.client import MESSAGE_TERMINATOR, MaxBridgeClient


class _FakeSocket:
    def __init__(self, response):
        self._response = response
        self._sent = []

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, payload):
        self._sent.append(payload)

    def recv(self, _size):
        if self._response is None:
            return b""
        response = self._response
        self._response = None
        return response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class MaxBridgeClientTests(unittest.TestCase):
    def test_send_command_accepts_stringified_matching_response_id(self):
        response = json.dumps(
            {"id": "1", "status": "success", "result": {"bridge_session_id": "session-1"}}
        ).encode("utf-8") + MESSAGE_TERMINATOR
        client = MaxBridgeClient()
        client._open_socket = lambda: _FakeSocket(response)

        result = client.send_command("find_device_session", {})

        self.assertEqual(result, {"bridge_session_id": "session-1"})


if __name__ == "__main__":
    unittest.main()
