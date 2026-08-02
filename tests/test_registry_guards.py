import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from livemcp import server
from livemcp.tools import max as max_tools
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
        expected_max_tools = {tool.__name__ for tool in max_tools.TOOLS}

        self.assertEqual(set(max_handlers.READ_HANDLERS), expected_max_tools)
        self.assertEqual(max_handlers.WRITE_HANDLERS, {})

    def test_all_max_tools_are_registered_on_mcp_server(self):
        for tool in max_tools.TOOLS:
            with self.subTest(tool=tool.__name__):
                self.assertIsNotNone(server.mcp._tool_manager.get_tool(tool.__name__))


if __name__ == "__main__":
    unittest.main()


class ReadmeDriftTests(unittest.TestCase):
    """The README quotes a tool count. Nothing regenerates it, so it drifts.

    A stale count is not cosmetic here — the number is the headline claim about
    what the server exposes, and it silently rots every time a tool is added.
    """

    def test_readme_tool_count_matches_registry(self):
        import re

        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text()
        claimed = re.findall(r"(\d+)\s+tools", readme)
        self.assertTrue(claimed, "README no longer states a tool count")

        # the live registry, not _collect_tools() — that helper takes the tool
        # groups as varargs and returns [] when called bare.
        actual = len(server.mcp._tool_manager._tools)
        for n in claimed:
            self.assertEqual(
                int(n), actual,
                f"README claims {n} tools, registry has {actual}. "
                "Update the README (or this test if the phrasing moved).",
            )

    def test_qa_workflow_doc_is_linked_from_readme(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / "docs/plugin-qa-workflow.md").exists())
        self.assertIn("docs/plugin-qa-workflow.md", (root / "README.md").read_text())
