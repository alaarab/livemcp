import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from livemcp.server import _collect_tools
from remote_script.LiveMCP.handlers import _merge_handler_dicts
from remote_script.LiveMCP.handlers import max as max_handlers


class RegistryGuardTests(unittest.TestCase):
    def test_collect_tools_rejects_duplicate_tool_names(self):
        def first_tool():
            return None

        def second_tool():
            return None

        second_tool.__name__ = first_tool.__name__

        with self.assertRaisesRegex(ValueError, "Duplicate tool registration"):
            _collect_tools([first_tool], [second_tool])

    def test_merge_handler_dicts_rejects_duplicate_commands(self):
        with self.assertRaisesRegex(ValueError, "Duplicate handler registrations"):
            _merge_handler_dicts({"duplicate": object()}, {"duplicate": object()})

    def test_max_bridge_commands_stay_off_main_thread_dispatch(self):
        expected_read_only = {
            "get_selected_max_device",
            "open_selected_device_in_max",
            "get_current_patcher",
            "list_patcher_boxes",
            "get_box_attrs",
            "set_box_attrs",
            "create_box",
            "create_patchline",
            "delete_box",
            "delete_patchline",
            "set_presentation_rect",
            "toggle_presentation_mode",
            "save_max_device",
        }

        self.assertTrue(expected_read_only.issubset(set(max_handlers.READ_HANDLERS)))
        self.assertFalse(expected_read_only & set(max_handlers.WRITE_HANDLERS))


if __name__ == "__main__":
    unittest.main()
