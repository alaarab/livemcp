import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp import installer


class InstallerTests(unittest.TestCase):
    @mock.patch("livemcp.installer.platform.system", return_value="Darwin")
    def test_find_all_ableton_discovers_and_sorts_available_apps(self, _platform_system):
        with tempfile.TemporaryDirectory() as temp_dir:
            applications_dir = Path(temp_dir)
            suite = applications_dir / "Ableton Live 12 Suite.app" / "Contents" / "App-Resources"
            intro = applications_dir / "Ableton Live 12 Intro.app" / "Contents" / "App-Resources"
            lite = applications_dir / "Ableton Live 11 Lite.app" / "Contents" / "App-Resources"
            for path in (suite, intro, lite):
                (path / "MIDI Remote Scripts").mkdir(parents=True)

            real_glob = Path.glob

            def fake_glob(path_obj, pattern):
                if path_obj == Path("/Applications") and pattern == "Ableton Live*.app":
                    return real_glob(applications_dir, pattern)
                return real_glob(path_obj, pattern)

            with mock.patch("livemcp.installer.Path.glob", autospec=True, side_effect=fake_glob):
                results = installer._find_all_ableton()

        self.assertEqual(
            [path.parents[2].stem for path in results],
            ["Ableton Live 12 Suite", "Ableton Live 12 Intro", "Ableton Live 11 Lite"],
        )

    @mock.patch("livemcp.installer._remove_old")
    @mock.patch("livemcp.installer.shutil.copytree")
    @mock.patch("livemcp.installer.os.symlink")
    @mock.patch("livemcp.installer._find_ableton")
    @mock.patch("livemcp.installer._get_remote_script_source")
    def test_install_copies_on_macos_by_default(
        self,
        get_remote_script_source,
        find_ableton,
        symlink,
        copytree,
        _remove_old,
    ):
        get_remote_script_source.return_value = Path("/tmp/LiveMCP")
        find_ableton.return_value = Path("/tmp/MIDI Remote Scripts"), "macos"

        with mock.patch.dict(os.environ, {}, clear=False):
            installer.install()

        copytree.assert_called_once_with(Path("/tmp/LiveMCP"), Path("/tmp/MIDI Remote Scripts/LiveMCP"))
        symlink.assert_not_called()


if __name__ == "__main__":
    unittest.main()
