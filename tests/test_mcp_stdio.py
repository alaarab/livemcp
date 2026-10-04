"""Exercise the public MCP protocol through the actual stdio server process."""

import json
import socketserver
import sys
import tempfile
import threading
import unittest
from pathlib import Path

import anyio
from mcp import Client, MCPError, StdioServerParameters


class BridgeHandler(socketserver.StreamRequestHandler):
    def handle(self):
        for line in self.rfile:
            request = json.loads(line)
            command = request["type"]
            response = {"id": request["id"], "status": "success"}
            if command == "get_session_info":
                response["result"] = {"tempo": 123.0, "track_count": 4}
            elif command == "get_livemcp_info":
                response["result"] = {"protocol_version": 3, "supports_request_ids": True}
            elif command == "get_song_time":
                response["result"] = {
                    "current_song_time": 12.5,
                    "can_undo": True,
                    "can_redo": False,
                }
            elif command == "get_track_info":
                response.update(status="error", error="Track index out of range")
            else:
                response.update(status="error", error=f"Unexpected command: {command}")
            self.wfile.write(json.dumps(response).encode() + b"\n")
            self.wfile.flush()


class MCPStdioTests(unittest.TestCase):
    def test_stdio_discovery_concurrent_calls_resources_and_errors(self):
        # Independent TCP peer, rather than a mock of the SDK or tool conversion.
        # Concurrent MCP tool/resource requests must share the Ableton socket safely.
        with socketserver.TCPServer(("127.0.0.1", 0), BridgeHandler) as bridge:
            thread = threading.Thread(target=bridge.serve_forever, daemon=True)
            thread.start()
            try:
                with tempfile.TemporaryDirectory() as docs_dir:
                    for mode in ("legacy", "auto"):
                        with self.subTest(mode=mode):
                            anyio.run(self._exercise, bridge.server_address[1], docs_dir, mode)
            finally:
                bridge.shutdown()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

    async def _exercise(self, port, docs_dir, mode):
        root = Path(__file__).resolve().parents[1]
        params = StdioServerParameters(
            command=sys.executable,
            args=[
                "-c",
                (
                    "from livemcp import connection, server; "
                    f"connection.PORT = {port}; server.main([])"
                ),
            ],
            env={"PYTHONPATH": str(root / "src"), "LIVEMCP_DOCS_DIR": docs_dir},
        )
        with anyio.fail_after(20):
            async with Client(params, mode=mode, cache=None, read_timeout_seconds=10) as connected:
                self.assertEqual(connected.server_info.name, "LiveMCP")
                if mode == "auto":
                    self.assertIsNone(connected.session.initialize_result)
                else:
                    self.assertIsNotNone(connected.session.initialize_result)
                client = connected.session
                tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                self.assertEqual(len(tools), 220)
                self.assertIn("tempo", tools["set_tempo"].input_schema["properties"])
                self.assertIn("tempo", tools["get_session_info"].output_schema["properties"])
                templates = await client.list_resource_templates()
                self.assertIn(
                    "live://track/{track_index}",
                    {template.uri_template for template in templates.resource_templates},
                )
                resources = await client.list_resources()
                self.assertIn("live://session/current", {r.uri for r in resources.resources})

                async def call_session():
                    result = await client.call_tool("get_session_info", {})
                    self.assertFalse(result.is_error)
                    self.assertEqual(result.structured_content, {"tempo": 123.0, "track_count": 4})
                    self.assertEqual(json.loads(result.content[0].text)["tempo"], 123.0)

                async def read_time():
                    result = await client.read_resource("live://song/time")
                    self.assertEqual(result.contents[0].mime_type, "application/json")
                    self.assertEqual(
                        json.loads(result.contents[0].text),
                        {
                            "current_song_time": 12.5,
                            "can_undo": True,
                            "can_redo": False,
                        },
                    )

                async with anyio.create_task_group() as group:
                    for _ in range(5):
                        group.start_soon(call_session)
                        group.start_soon(read_time)
                docs = await client.read_resource("docs://status")
                self.assertEqual(json.loads(docs.contents[0].text)["total_pages"], 0)
                error = await client.call_tool("get_track_info", {"track_index": -1})
                self.assertTrue(error.is_error)
                self.assertIn("Track index out of range", error.content[0].text)
                with self.assertRaisesRegex(MCPError, "Track index out of range"):
                    await client.read_resource("live://track/-1")
                invalid = await client.call_tool("set_tempo", {"tempo": "not a number"})
                self.assertTrue(invalid.is_error)
