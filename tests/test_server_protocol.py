import json
import unittest

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
            b'{"type":"ping","params":{"value":1}}\n'
            b'{"type":"ping","params":{"value":2}}\n'
        )
        client = FakeClient([payload, b""])

        server._handle_client(client)

        responses = [json.loads(item.decode("utf-8")) for item in client.sent]
        self.assertEqual(
            responses,
            [
                {"status": "success", "result": {"pong": 1}},
                {"status": "success", "result": {"pong": 2}},
            ],
        )
        self.assertTrue(all(item.endswith(b"\n") for item in client.sent))
        self.assertTrue(client.closed)

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
