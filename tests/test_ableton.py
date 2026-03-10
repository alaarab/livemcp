import unittest
from unittest import mock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp import ableton


class QuitAbletonTests(unittest.TestCase):
    @mock.patch("livemcp.ableton.time.sleep", return_value=None)
    @mock.patch("livemcp.ableton.wait_for_dialog", return_value=None)
    @mock.patch("livemcp.ableton._dismiss_quit_dialog_via_livemcp", return_value=False)
    @mock.patch("livemcp.ableton.is_process_running", side_effect=[True, False])
    @mock.patch("livemcp.ableton._launch_osascript")
    @mock.patch("livemcp.ableton.find_ableton_app", return_value="Ableton Live 12 Suite")
    def test_quit_ableton_launches_quit_script_asynchronously(
        self,
        _find_ableton_app,
        launch_osascript,
        _is_process_running,
        dismiss_quit_dialog,
        wait_for_dialog,
        _sleep,
    ):
        ableton.quit_ableton(force=True)

        launch_osascript.assert_called_once_with('tell application "Ableton Live 12 Suite" to quit')
        dismiss_quit_dialog.assert_called()
        wait_for_dialog.assert_called()


if __name__ == "__main__":
    unittest.main()
