import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from remote_script.LiveMCP.errors import LiveMCPError
from remote_script.LiveMCP.server import LiveMCPServer


class FakeControlSurface:
    def log_message(self, _message):
        return None

    def schedule_message(self, _delay, callback):
        callback()


class FakeClient:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.sent = []
        self.closed = False

    def recv(self, _size):
        if self._chunks:
            return self._chunks.pop(0)
        return b""

    def sendall(self, payload):
        self.sent.append(payload)

    def close(self):
        self.closed = True

    def fileno(self):
        return -1 if self.closed else 3

    def shutdown(self, _how):
        self.closed = True


class FakeThread:
    def __init__(self):
        self.join_calls = []

    def join(self, timeout=None):
        self.join_calls.append(timeout)

    def is_alive(self):
        return False


class ServerProtocolTests(unittest.TestCase):
    def test_handle_client_processes_multiple_newline_delimited_commands(self):
        server = LiveMCPServer(FakeControlSurface())
        server._running = True
        server._read_handlers = {
            "ping": lambda _cs, params: {"pong": params["value"]},
        }
        server._write_handlers = {}

        payload = (
            b'{"id":1,"type":"ping","params":{"value":1}}\n'
            b'{"id":2,"type":"ping","params":{"value":2}}\n'
        )
        client = FakeClient([payload, b""])

        server._handle_client(client)

        responses = [json.loads(item.decode("utf-8")) for item in client.sent]
        self.assertEqual(
            responses,
            [
                {"id": 1, "status": "success", "result": {"pong": 1}},
                {"id": 2, "status": "success", "result": {"pong": 2}},
            ],
        )
        self.assertTrue(all(item.endswith(b"\n") for item in client.sent))
        self.assertTrue(client.closed)

    def test_handle_client_echoes_request_id_on_errors(self):
        server = LiveMCPServer(FakeControlSurface())
        server._running = True
        server._read_handlers = {}
        server._write_handlers = {}
        client = FakeClient([b'{"id":9,"type":"missing","params":{}}\n', b""])

        server._handle_client(client)

        responses = [json.loads(item.decode("utf-8")) for item in client.sent]
        self.assertEqual(
            responses,
            [{"id": 9, "status": "error", "error": "Unknown command: missing"}],
        )

    def test_handle_client_preserves_structured_write_errors(self):
        server = LiveMCPServer(FakeControlSurface())
        server._running = True
        server._read_handlers = {}

        def explode(_cs, _params):
            raise LiveMCPError(
                "max/not-max-device",
                "Selected device is not a Max for Live device.",
                {"device_name": "EQ Eight"},
            )

        server._write_handlers = {"explode": explode}
        client = FakeClient([b'{"id":4,"type":"explode","params":{}}\n', b""])

        server._handle_client(client)

        responses = [json.loads(item.decode("utf-8")) for item in client.sent]
        self.assertEqual(
            responses,
            [
                {
                    "id": 4,
                    "status": "error",
                    "error": {
                        "code": "max/not-max-device",
                        "message": "Selected device is not a Max for Live device.",
                        "details": {"device_name": "EQ Eight"},
                    },
                }
            ],
        )

    def test_stop_closes_client_sockets_and_joins_threads(self):
        server = LiveMCPServer(FakeControlSurface())
        server._running = True
        server_socket = FakeClient([])
        client = FakeClient([])
        server_thread = FakeThread()
        client_thread = FakeThread()
        server._server_socket = server_socket
        server._server_thread = server_thread
        server._client_sockets = [client]
        server._client_threads = [client_thread]

        server.stop()

        self.assertFalse(server._running)
        self.assertTrue(server_socket.closed)
        self.assertTrue(client.closed)
        self.assertEqual(server_thread.join_calls, [2.0])
        self.assertEqual(client_thread.join_calls, [2.0])


if __name__ == "__main__":
    unittest.main()
