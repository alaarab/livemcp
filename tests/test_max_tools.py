import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp import server
from livemcp.tools import max as max_tools


class MaxToolTests(unittest.TestCase):
    @mock.patch("livemcp.tools.max.get_connection")
    def test_get_selected_max_device_returns_structured_data(self, get_connection):
        get_connection.return_value.send_command.return_value = {
            "supported": True,
            "bridge_attached": True,
            "bridge_session_id": "session-1",
            "selected_device": {"device_name": "My Max Device"},
        }

        result = max_tools.get_selected_max_device()

        self.assertTrue(result["supported"])
        self.assertEqual(result["bridge_session_id"], "session-1")
        self.assertEqual(result["selected_device"]["device_name"], "My Max Device")

    @mock.patch("livemcp.tools.max.get_connection")
    def test_create_box_serializes_mutation_result_and_params(self, get_connection):
        get_connection.return_value.send_command.return_value = {
            "box_id": "obj-7",
            "created": True,
        }

        payload = json.loads(
            max_tools.create_box(
                "newobj",
                100,
                200,
                args=["cycle~", 440],
                object_attrs={"text": "cycle~ 440"},
                box_attrs={"patching_rect": [100, 200, 60, 22]},
                bridge_session_id="session-1",
            )
        )

        get_connection.return_value.send_command.assert_called_once_with(
            "create_box",
            {
                "bridge_session_id": "session-1",
                "classname": "newobj",
                "left": 100,
                "top": 200,
                "args": ["cycle~", 440],
                "object_attrs": {"text": "cycle~ 440"},
                "box_attrs": {"patching_rect": [100, 200, 60, 22]},
            },
        )
        self.assertEqual(payload["box_id"], "obj-7")

    @mock.patch("livemcp.tools.max.get_connection")
    def test_get_box_attrs_includes_box_id(self, get_connection):
        get_connection.return_value.send_command.return_value = {
            "bridge_session_id": "session-1",
            "box_id": "obj-3",
            "object_attrs": {"text": "gain~"},
            "box_attrs": {"patching_rect": [10, 20, 50, 20]},
        }

        result = max_tools.get_box_attrs("obj-3", bridge_session_id="session-1")

        get_connection.return_value.send_command.assert_called_once_with(
            "get_box_attrs",
            {"bridge_session_id": "session-1", "box_id": "obj-3"},
        )
        self.assertEqual(result["box_id"], "obj-3")

    def test_max_tools_publish_output_schema(self):
        structured_tools = [
            "get_selected_max_device",
            "get_current_patcher",
            "list_patcher_boxes",
            "get_box_attrs",
        ]

        for tool_name in structured_tools:
            with self.subTest(tool_name=tool_name):
                tool = server.mcp._tool_manager.get_tool(tool_name)
                self.assertIsNotNone(tool.output_schema)


if __name__ == "__main__":
    unittest.main()
