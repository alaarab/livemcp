import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from remote_script.LiveMCP.errors import LiveMCPError
from remote_script.LiveMCP.max_bridge.client import (
    BRIDGE_PROTOCOL_VERSION,
    MESSAGE_TERMINATOR,
    MaxBridgeClient,
)


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
        fake_socket = _FakeSocket(response)
        client = MaxBridgeClient()
        client._open_socket = lambda: fake_socket

        result = client.send_command("find_device_session", {})

        self.assertEqual(result, {"bridge_session_id": "session-1"})
        request = json.loads(fake_socket._sent[0].decode("utf-8"))
        self.assertEqual(request["id"], 1)
        self.assertEqual(request["protocol_version"], BRIDGE_PROTOCOL_VERSION)

    def test_send_command_rejects_missing_response_id(self):
        response = json.dumps(
            {"status": "success", "result": {"bridge_session_id": "session-1"}}
        ).encode("utf-8") + MESSAGE_TERMINATOR
        client = MaxBridgeClient()
        client._open_socket = lambda: _FakeSocket(response)

        with self.assertRaises(LiveMCPError) as raised:
            client.send_command("find_device_session", {})

        self.assertEqual(raised.exception.code, "max/protocol-error")
        self.assertEqual(raised.exception.details["expected_id"], 1)
        self.assertIsNone(raised.exception.details["response_id"])

    def test_send_command_rejects_mismatched_response_id(self):
        response = json.dumps(
            {"id": 99, "status": "success", "result": {}}
        ).encode("utf-8") + MESSAGE_TERMINATOR
        client = MaxBridgeClient()
        client._open_socket = lambda: _FakeSocket(response)

        with self.assertRaises(LiveMCPError) as raised:
            client.send_command("find_device_session", {})

        self.assertEqual(raised.exception.code, "max/protocol-error")
        self.assertEqual(
            raised.exception.details,
            {"expected_id": 1, "response_id": 99},
        )

    def test_send_command_maps_structured_bridge_error(self):
        response = json.dumps(
            {
                "id": 1,
                "status": "error",
                "error": {
                    "code": "max/unsupported-attr",
                    "message": "Unsupported object attribute.",
                    "details": {"attr": "filename"},
                },
            }
        ).encode("utf-8") + MESSAGE_TERMINATOR
        client = MaxBridgeClient()
        client._open_socket = lambda: _FakeSocket(response)

        with self.assertRaises(LiveMCPError) as raised:
            client.send_command("set_box_attrs", {})

        self.assertEqual(raised.exception.code, "max/unsupported-attr")
        self.assertEqual(raised.exception.details, {"attr": "filename"})

    def test_get_info_rejects_unsupported_protocol_version(self):
        response = json.dumps(
            {
                "id": 1,
                "status": "success",
                "result": {"reachable": True, "protocol_version": 2},
            }
        ).encode("utf-8") + MESSAGE_TERMINATOR
        client = MaxBridgeClient()
        client._open_socket = lambda: _FakeSocket(response)

        result = client.get_info()

        self.assertFalse(result["reachable"])
        self.assertEqual(result["error_code"], "max/protocol-version-mismatch")


if __name__ == "__main__":
    unittest.main()
