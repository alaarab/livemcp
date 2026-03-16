import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from remote_script.LiveMCP.errors import LiveMCPError
from remote_script.LiveMCP.handlers import max as max_handlers


class MaxHandlerTests(unittest.TestCase):
    @mock.patch("remote_script.LiveMCP.handlers.max._resolve_bridge_session")
    def test_list_patcher_boxes_falls_back_to_named_only_after_bridge_timeout(
        self, resolve_bridge_session
    ):
        bridge_client = mock.Mock()
        bridge_client.send_command.side_effect = [
            {"box_count": 24},
            LiveMCPError("max/bridge-timeout", "Timed out waiting for Max bridge response."),
            {"boxes": [{"box_id": "state_js", "varname": "state_js"}]},
        ]
        resolve_bridge_session.return_value = (
            {"selected_device": {"device_name": "Linear Phase EQ Probe"}},
            bridge_client,
            {"bridge_session_id": "session-1"},
        )

        result = max_handlers.list_patcher_boxes(mock.sentinel.control_surface, {})

        self.assertEqual(result["bridge_session_id"], "session-1")
        self.assertEqual(result["total_box_count"], 24)
        self.assertFalse(result["complete"])
        self.assertEqual(result["enumeration_mode"], "named_only")
        self.assertEqual(result["fallback_reason"], "max/bridge-timeout")
        self.assertEqual(result["boxes"][0]["box_id"], "state_js")
        self.assertEqual(
            bridge_client.send_command.call_args_list,
            [
                mock.call(
                    "get_current_patcher",
                    {
                        "bridge_session_id": "session-1",
                        "device_fingerprint": {"device_name": "Linear Phase EQ Probe"},
                    },
                ),
                mock.call(
                    "list_boxes",
                    {
                        "bridge_session_id": "session-1",
                        "device_fingerprint": {"device_name": "Linear Phase EQ Probe"},
                    },
                ),
                mock.call(
                    "list_named_boxes",
                    {
                        "bridge_session_id": "session-1",
                        "device_fingerprint": {"device_name": "Linear Phase EQ Probe"},
                    },
                ),
            ],
        )

    @mock.patch("remote_script.LiveMCP.handlers.max._resolve_bridge_session")
    def test_list_patcher_boxes_supports_named_only_request(self, resolve_bridge_session):
        bridge_client = mock.Mock()
        bridge_client.send_command.side_effect = [
            {"box_count": 12},
            {"boxes": [{"box_id": "lpeq_display", "varname": "lpeq_display"}]},
        ]
        resolve_bridge_session.return_value = (
            {"selected_device": {"device_name": "Linear Phase EQ Probe"}},
            bridge_client,
            {"bridge_session_id": "session-2"},
        )

        result = max_handlers.list_patcher_boxes(
            mock.sentinel.control_surface,
            {"named_only": True},
        )

        self.assertEqual(result["bridge_session_id"], "session-2")
        self.assertEqual(result["total_box_count"], 12)
        self.assertFalse(result["complete"])
        self.assertEqual(result["enumeration_mode"], "named_only")
        self.assertNotIn("fallback_reason", result)
        self.assertEqual(result["boxes"][0]["box_id"], "lpeq_display")
        self.assertEqual(
            bridge_client.send_command.call_args_list,
            [
                mock.call(
                    "get_current_patcher",
                    {
                        "bridge_session_id": "session-2",
                        "device_fingerprint": {"device_name": "Linear Phase EQ Probe"},
                    },
                ),
                mock.call(
                    "list_named_boxes",
                    {
                        "bridge_session_id": "session-2",
                        "device_fingerprint": {"device_name": "Linear Phase EQ Probe"},
                    },
                ),
            ],
        )

    @mock.patch("remote_script.LiveMCP.handlers.max._resolve_bridge_session")
    def test_list_patcher_boxes_uses_named_only_mode_for_large_patchers(
        self, resolve_bridge_session
    ):
        bridge_client = mock.Mock()
        bridge_client.send_command.side_effect = [
            {"box_count": max_handlers.FULL_BOX_LIST_THRESHOLD + 1},
            {"boxes": [{"box_id": "lpeq_display", "varname": "lpeq_display"}]},
        ]
        resolve_bridge_session.return_value = (
            {"selected_device": {"device_name": "Linear Phase EQ Probe"}},
            bridge_client,
            {"bridge_session_id": "session-3"},
        )

        result = max_handlers.list_patcher_boxes(mock.sentinel.control_surface, {})

        self.assertEqual(result["bridge_session_id"], "session-3")
        self.assertEqual(result["total_box_count"], max_handlers.FULL_BOX_LIST_THRESHOLD + 1)
        self.assertFalse(result["complete"])
        self.assertEqual(result["enumeration_mode"], "named_only")
        self.assertEqual(result["fallback_reason"], "max/box-count-threshold")
        self.assertEqual(result["boxes"][0]["box_id"], "lpeq_display")
        self.assertEqual(
            bridge_client.send_command.call_args_list,
            [
                mock.call(
                    "get_current_patcher",
                    {
                        "bridge_session_id": "session-3",
                        "device_fingerprint": {"device_name": "Linear Phase EQ Probe"},
                    },
                ),
                mock.call(
                    "list_named_boxes",
                    {
                        "bridge_session_id": "session-3",
                        "device_fingerprint": {"device_name": "Linear Phase EQ Probe"},
                    },
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
