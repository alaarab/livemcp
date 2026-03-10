import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp import server
from livemcp.tools import session


class SessionToolTests(unittest.TestCase):
    @mock.patch("livemcp.tools.session.get_connection")
    def test_get_session_info_returns_structured_data(self, get_connection):
        get_connection.return_value.send_command.return_value = {
            "tempo": 120.0,
            "is_playing": True,
            "track_count": 8,
        }

        result = session.get_session_info()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["tempo"], 120.0)
        self.assertTrue(result["is_playing"])

    @mock.patch("livemcp.tools.session.get_connection")
    @mock.patch("livemcp.tools.session.probe_command")
    @mock.patch("livemcp.tools.session.get_install_status")
    def test_get_livemcp_status_combines_local_and_remote_state(
        self,
        get_install_status,
        probe_command,
        get_connection,
    ):
        get_install_status.return_value = {
            "installed": True,
            "needs_install": False,
            "install_mode": "copy",
        }
        probe_command.return_value = {
            "protocol_version": 2,
            "supports_request_ids": True,
            "transport": "tcp-json-lines",
        }
        get_connection.return_value.get_server_info.return_value = {
            "protocol_version": 2,
            "supports_request_ids": True,
            "transport": "tcp-json-lines",
            "legacy_compatibility_mode": False,
        }

        result = session.get_livemcp_status()

        self.assertTrue(result["remote_reachable"])
        self.assertEqual(result["remote_info"]["protocol_version"], 2)
        self.assertEqual(result["warnings"], [])

    @mock.patch("livemcp.tools.session.get_connection")
    @mock.patch("livemcp.tools.session.probe_command")
    @mock.patch("livemcp.tools.session.get_install_status")
    def test_get_livemcp_status_treats_legacy_remote_as_reachable(
        self,
        get_install_status,
        probe_command,
        get_connection,
    ):
        get_install_status.return_value = {
            "installed": True,
            "needs_install": False,
            "install_mode": "copy",
        }
        probe_command.side_effect = RuntimeError("Unknown command: get_livemcp_info")
        get_connection.return_value.get_server_info.return_value = None

        result = session.get_livemcp_status()

        self.assertTrue(result["remote_reachable"])
        self.assertEqual(result["remote_info"]["protocol_version"], 1)
        self.assertIsNone(result["remote_error"])
        self.assertIn(
            "Ableton is running an older LiveMCP transport protocol; reinstall and restart Ableton.",
            result["warnings"],
        )
        self.assertNotIn("LiveMCP socket is not currently reachable.", result["warnings"])

    def test_controller_tools_publish_output_schema(self):
        structured_tools = [
            "get_session_info",
            "get_livemcp_status",
            "get_view_state",
            "get_selected_track",
            "get_selected_scene",
            "get_selected_device",
        ]

        for tool_name in structured_tools:
            with self.subTest(tool_name=tool_name):
                tool = server.mcp._tool_manager.get_tool(tool_name)
                self.assertIsNotNone(tool.output_schema)


if __name__ == "__main__":
    unittest.main()
