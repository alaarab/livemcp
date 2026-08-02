import socket
import threading
import time
import unittest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp.connection import AbletonConnection, MESSAGE_TERMINATOR
from livemcp.errors import RemoteCommandError


def _always_readable_fd(owner):
    """An fd that select() always reports ready.

    connection.py select()s on the socket before recv (WSL2 compat, ecd41a3),
    so a socket double must expose a real descriptor or select raises
    TypeError. A socketpair with a byte already in the pipe is always ready,
    which hands control straight back to the double's own recv().
    """
    rd, wr = socket.socketpair()
    wr.sendall(b"\x00")
    owner._fd_pair = (rd, wr)          # keep alive for the object's lifetime
    return rd.fileno()


class BlockingFakeSocket:
    def __init__(self):
        self._readable_fd = _always_readable_fd(self)
        self.first_send_started = threading.Event()
        self.release_first_send = threading.Event()
        self.first_send = True
        self.concurrent_send_detected = False
        self._sending = False
        self._responses = []
        self.sent_payloads = []

    def fileno(self):
        # connection.py select()s on the socket (WSL2 compat, ecd41a3), and
        # select.select requires a real file descriptor. Hand it one from a
        # throwaway socketpair that is always readable, so select returns
        # immediately and the double's own recv() drives the test.
        return self._readable_fd

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, payload):
        if self._sending:
            self.concurrent_send_detected = True
        self._sending = True
        try:
            self.sent_payloads.append(payload)
            request = json.loads(payload.rstrip(MESSAGE_TERMINATOR).decode("utf-8"))
            if self.first_send:
                self.first_send = False
                self.first_send_started.set()
                self.release_first_send.wait(timeout=1.0)
            self._responses.append(
                json.dumps(
                    {"id": request["id"], "status": "success", "result": {"ok": True}}
                ).encode("utf-8")
                + MESSAGE_TERMINATOR
            )
        finally:
            self._sending = False

    def recv(self, _size):
        deadline = time.time() + 1.0
        while not self._responses and time.time() < deadline:
            time.sleep(0.01)
        if not self._responses:
            return b""
        return self._responses.pop(0)

    def close(self):
        return None


class ScriptedFakeSocket:
    def __init__(self, response_builder):
        self._readable_fd = _always_readable_fd(self)
        self._response_builder = response_builder
        self._responses = []
        self.sent_payloads = []
        self.closed = False

    def fileno(self):
        # connection.py select()s on the socket (WSL2 compat, ecd41a3), and
        # select.select requires a real file descriptor. Hand it one from a
        # throwaway socketpair that is always readable, so select returns
        # immediately and the double's own recv() drives the test.
        return self._readable_fd

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, payload):
        self.sent_payloads.append(payload)
        request = json.loads(payload.rstrip(MESSAGE_TERMINATOR).decode("utf-8"))
        response = self._response_builder(request, len(self.sent_payloads))
        if response is not None:
            self._responses.append(json.dumps(response).encode("utf-8") + MESSAGE_TERMINATOR)

    def recv(self, _size):
        if not self._responses:
            return b""
        return self._responses.pop(0)

    def close(self):
        self.closed = True


class AbletonConnectionTests(unittest.TestCase):
    def test_send_command_serializes_access_to_shared_socket(self):
        connection = AbletonConnection()
        fake_socket = BlockingFakeSocket()
        connection._socket = fake_socket

        results = []
        exceptions = []

        def run_command():
            try:
                results.append(connection.send_command("ping", {}))
            except Exception as exc:  # pragma: no cover - test should stay clean
                exceptions.append(exc)

        thread_one = threading.Thread(target=run_command)
        thread_two = threading.Thread(target=run_command)

        thread_one.start()
        self.assertTrue(fake_socket.first_send_started.wait(timeout=1.0))
        thread_two.start()
        time.sleep(0.1)
        fake_socket.release_first_send.set()

        thread_one.join(timeout=1.0)
        thread_two.join(timeout=1.0)

        self.assertFalse(exceptions)
        self.assertEqual(len(results), 2)
        self.assertFalse(fake_socket.concurrent_send_detected)
        self.assertTrue(all(payload.endswith(MESSAGE_TERMINATOR) for payload in fake_socket.sent_payloads))
        payload_ids = [json.loads(payload.rstrip(MESSAGE_TERMINATOR).decode("utf-8"))["id"] for payload in fake_socket.sent_payloads]
        self.assertEqual(payload_ids, [1, 2])

    def test_send_command_retries_after_response_id_mismatch(self):
        connection = AbletonConnection()

        socket_one = ScriptedFakeSocket(
            lambda request, _send_count: (
                {"id": request["id"], "status": "success", "result": {"tempo": 120.0}}
                if request["type"] == "get_session_info"
                else {
                    "id": request["id"],
                    "status": "success",
                    "result": {
                        "protocol_version": 3,
                        "supports_request_ids": True,
                        "transport": "tcp-json-lines",
                        "namespaces": ["live", "docs", "max"],
                        "max_bridge": {"reachable": False},
                    },
                }
                if request["type"] == "get_livemcp_info"
                else {"id": 999, "status": "success", "result": {"ok": "wrong"}}
            )
        )
        socket_two = ScriptedFakeSocket(
            lambda request, _send_count: {
                "id": request["id"],
                "status": "success",
                "result": {"ok": request["type"]},
            }
        )

        sockets = iter([socket_one, socket_two])
        connection._open_socket = lambda: next(sockets)

        original_sleep = time.sleep
        try:
            time.sleep = lambda _seconds: None
            result = connection.send_command("ping", {"value": 1})
        finally:
            time.sleep = original_sleep

        self.assertEqual(result, {"ok": "ping"})
        self.assertTrue(socket_one.closed)
        command_ids = []
        for fake_socket in (socket_one, socket_two):
            for payload in fake_socket.sent_payloads:
                command = json.loads(payload.rstrip(MESSAGE_TERMINATOR).decode("utf-8"))
                if command["type"] == "ping":
                    command_ids.append(command["id"])

        self.assertEqual(command_ids, [1, 1])

    def test_send_command_accepts_legacy_response_without_request_id(self):
        connection = AbletonConnection()
        connection._socket = ScriptedFakeSocket(
            lambda _request, _send_count: {"status": "success", "result": {"ok": "legacy"}}
        )

        result = connection.send_command("ping", {})

        self.assertEqual(result, {"ok": "legacy"})

    def test_connect_records_server_info_when_supported(self):
        connection = AbletonConnection()
        connection._open_socket = lambda: ScriptedFakeSocket(
            lambda request, _send_count: (
                {
                    "id": request["id"],
                    "status": "success",
                    "result": {"tempo": 120.0},
                }
                if request["type"] == "get_session_info"
                else {
                    "id": request["id"],
                    "status": "success",
                    "result": {
                        "protocol_version": 3,
                        "supports_request_ids": True,
                        "transport": "tcp-json-lines",
                        "namespaces": ["live", "docs", "max"],
                        "max_bridge": {"reachable": True},
                    },
                }
            )
        )

        connection.connect()

        self.assertEqual(
            connection.get_server_info(),
            {
                "protocol_version": 3,
                "supports_request_ids": True,
                "transport": "tcp-json-lines",
                "namespaces": ["live", "docs", "max"],
                "max_bridge": {"reachable": True},
                "legacy_compatibility_mode": False,
            },
        )

    def test_connect_falls_back_to_legacy_server_info(self):
        connection = AbletonConnection()
        connection._open_socket = lambda: ScriptedFakeSocket(
            lambda request, _send_count: (
                {
                    "id": request["id"],
                    "status": "success",
                    "result": {"tempo": 120.0},
                }
                if request["type"] == "get_session_info"
                else {
                    "status": "error",
                    "error": "Unknown command: get_livemcp_info",
                }
            )
        )

        connection.connect()

        self.assertEqual(
            connection.get_server_info(),
            {
                "protocol_version": 1,
                "supports_request_ids": False,
                "transport": "tcp-json-lines",
                "legacy_compatibility_mode": True,
            },
        )

    def test_send_command_raises_structured_remote_error(self):
        connection = AbletonConnection()
        connection._socket = ScriptedFakeSocket(
            lambda request, _send_count: {
                "id": request["id"],
                "status": "error",
                "error": {
                    "code": "max/not-max-device",
                    "message": "Selected device is not a Max for Live device.",
                    "details": {"device_name": "EQ Eight"},
                },
            }
        )

        with self.assertRaises(RemoteCommandError) as raised:
            connection.send_command("get_current_patcher", {})

        self.assertEqual(raised.exception.code, "max/not-max-device")
        self.assertEqual(
            raised.exception.details,
            {"device_name": "EQ Eight"},
        )


if __name__ == "__main__":
    unittest.main()
