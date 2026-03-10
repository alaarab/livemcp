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


if __name__ == "__main__":
    unittest.main()
