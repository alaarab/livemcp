import threading
import time
import unittest
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
            if self.first_send:
                self.first_send = False
                self.first_send_started.set()
                self.release_first_send.wait(timeout=1.0)
            self._responses.append(b'{"status":"success","result":{"ok":true}}\n')
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


if __name__ == "__main__":
    unittest.main()
