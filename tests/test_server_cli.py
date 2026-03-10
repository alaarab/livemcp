import io
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp import server


class ServerCliTests(unittest.TestCase):
    @mock.patch("livemcp.server.mcp.run")
    def test_main_runs_stdio_server_without_flags(self, run_server):
        server.main([])
        run_server.assert_called_once_with(transport="stdio")

    @mock.patch("livemcp.ableton.quit_ableton")
    def test_main_passes_no_force_to_quit_helper(self, quit_ableton):
        with mock.patch("sys.stdout", new=io.StringIO()):
            server.main(["--quit-ableton", "--no-force"])
        quit_ableton.assert_called_once_with(force=False)

    def test_main_rejects_no_force_without_quit(self):
        with self.assertRaises(SystemExit) as context:
            with mock.patch("sys.stderr", new=io.StringIO()):
                server.main(["--no-force"])

        self.assertEqual(context.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
