import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp.server import _collect_tools
from remote_script.LiveMCP.handlers import _merge_handler_dicts


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


if __name__ == "__main__":
    unittest.main()
