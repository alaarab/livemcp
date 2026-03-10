import unittest
from pathlib import Path
import sys
import tempfile
from unittest import mock

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

    def test_find_remote_script_dir_prefers_packaged_layout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_dir = temp_path / "package"
            repo_root = temp_path / "repo"
            packaged_remote_script = package_dir / "remote_script"
            repo_remote_script = repo_root / "remote_script"
            packaged_remote_script.mkdir(parents=True)
            repo_remote_script.mkdir(parents=True)

            found = ableton._find_remote_script_dir(repo_root=repo_root, package_dir=package_dir)

        self.assertEqual(found, packaged_remote_script)

    def test_find_ableton_preferences_dir_prefers_matching_app_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prefs_root = Path(temp_dir)
            latest_other = prefs_root / "Live 12.3.1"
            matching = prefs_root / "Live 11.3.25"
            older_matching = prefs_root / "Live 11.2.10"
            for path in (latest_other, matching, older_matching):
                path.mkdir(parents=True)

            found = ableton.find_ableton_preferences_dir(
                app_name="Ableton Live 11 Suite",
                prefs_root=prefs_root,
            )

        self.assertEqual(found, matching)


if __name__ == "__main__":
    unittest.main()
