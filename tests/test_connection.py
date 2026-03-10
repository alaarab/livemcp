import threading
import time
import unittest
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp.connection import AbletonConnection, MESSAGE_TERMINATOR


class BlockingFakeSocket:
    def __init__(self):
        self.first_send_started = threading.Event()
        self.release_first_send = threading.Event()
        self.first_send = True
        self.concurrent_send_detected = False
        self._sending = False
        self._responses = []
        self.sent_payloads = []

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
        self._response_builder = response_builder
        self._responses = []
        self.sent_payloads = []
        self.closed = False

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
            lambda request, send_count: (
                {"id": request["id"], "status": "success", "result": {"ok": "ping"}}
                if send_count == 1
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
        command_ids = [
            json.loads(payload.rstrip(MESSAGE_TERMINATOR).decode("utf-8"))["id"]
            for payload in (socket_one.sent_payloads[1], socket_two.sent_payloads[1])
        ]
        self.assertEqual(command_ids, [1, 1])

    def test_send_command_accepts_legacy_response_without_request_id(self):
        connection = AbletonConnection()
        connection._socket = ScriptedFakeSocket(
            lambda _request, _send_count: {"status": "success", "result": {"ok": "legacy"}}
        )

        result = connection.send_command("ping", {})

        self.assertEqual(result, {"ok": "legacy"})


if __name__ == "__main__":
    unittest.main()
