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
    @mock.patch("livemcp.installer._copy_remote_script")
    @mock.patch("livemcp.installer.os.symlink")
    @mock.patch("livemcp.installer._find_ableton")
    @mock.patch("livemcp.installer._get_remote_script_source")
    def test_install_copies_on_macos_by_default(
        self,
        get_remote_script_source,
        find_ableton,
        symlink,
        copy_remote_script,
        _remove_old,
    ):
        get_remote_script_source.return_value = Path("/tmp/LiveMCP")
        find_ableton.return_value = Path("/tmp/MIDI Remote Scripts"), "macos"

        with mock.patch.dict(os.environ, {}, clear=False):
            installer.install()

        copy_remote_script.assert_called_once_with(
            Path("/tmp/LiveMCP"),
            Path("/tmp/MIDI Remote Scripts/LiveMCP"),
        )
        symlink.assert_not_called()

    @mock.patch("livemcp.installer._remove_old")
    @mock.patch("livemcp.installer.shutil.copytree")
    @mock.patch("livemcp.installer.os.symlink")
    @mock.patch("livemcp.installer._find_ableton")
    @mock.patch("livemcp.installer._get_remote_script_source")
    def test_install_uses_symlink_when_requested_on_macos(
        self,
        get_remote_script_source,
        find_ableton,
        symlink,
        copytree,
        _remove_old,
    ):
        get_remote_script_source.return_value = Path("/tmp/LiveMCP")
        find_ableton.return_value = Path("/tmp/MIDI Remote Scripts"), "macos"

        installer.install(use_symlink=True)

        symlink.assert_called_once_with(Path("/tmp/LiveMCP"), Path("/tmp/MIDI Remote Scripts/LiveMCP"))
        copytree.assert_not_called()

    @mock.patch("livemcp.installer._remove_old")
    @mock.patch("livemcp.installer._find_ableton")
    @mock.patch("livemcp.installer._get_remote_script_source")
    def test_install_rejects_symlink_request_before_removing_existing_install(
        self,
        get_remote_script_source,
        find_ableton,
        remove_old,
    ):
        get_remote_script_source.return_value = Path("/tmp/LiveMCP")
        find_ableton.return_value = Path("/tmp/MIDI Remote Scripts"), "windows"

        with self.assertRaises(SystemExit):
            installer.install(use_symlink=True)

        remove_old.assert_not_called()

    @mock.patch("livemcp.installer._find_ableton")
    @mock.patch("livemcp.installer._get_remote_script_source")
    def test_get_install_status_reports_out_of_sync_copy(self, get_remote_script_source, find_ableton):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "source"
            target = temp_path / "target"
            dest = target / "LiveMCP"
            source.mkdir(parents=True)
            dest.mkdir(parents=True)
            (source / "__init__.py").write_text("a = 1\n", encoding="utf-8")
            (dest / "__init__.py").write_text("a = 2\n", encoding="utf-8")
            get_remote_script_source.return_value = source
            find_ableton.return_value = target, "macos"

            status = installer.get_install_status()

        self.assertTrue(status["installed"])
        self.assertEqual(status["install_mode"], "copy")
        self.assertFalse(status["in_sync"])
        self.assertTrue(status["needs_install"])

    @mock.patch("livemcp.installer._remove_old")
    @mock.patch("livemcp.installer._find_ableton")
    @mock.patch("livemcp.installer._get_remote_script_source")
    def test_install_copy_ignores_pycache(self, get_remote_script_source, find_ableton, _remove_old):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "source"
            target = temp_path / "target"
            source.mkdir(parents=True)
            (source / "__init__.py").write_text("a = 1\n", encoding="utf-8")
            (source / "__pycache__").mkdir()
            (source / "__pycache__" / "module.cpython-311.pyc").write_bytes(b"compiled")
            get_remote_script_source.return_value = source
            find_ableton.return_value = target, "macos"

            installer.install(use_symlink=False)

            self.assertTrue((target / "LiveMCP" / "__init__.py").exists())
            self.assertFalse((target / "LiveMCP" / "__pycache__").exists())

    def test_install_max_bridge_writes_probe_device_and_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            result = installer.install_max_bridge(root=root)

            self.assertTrue(Path(result["device_path"]).exists())
            self.assertTrue(result["device_path"].endswith(".amxd"))
            for asset_path in result["asset_paths"]:
                self.assertTrue(Path(asset_path).exists())

    def test_get_max_bridge_status_reports_probe_install(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            before = installer.get_max_bridge_status(root=root)
            self.assertFalse(before["probe_device_installed"])

            installer.install_max_bridge(root=root)
            after = installer.get_max_bridge_status(root=root)

            self.assertTrue(after["probe_device_installed"])
            self.assertTrue(after["probe_assets_installed"])


if __name__ == "__main__":
    unittest.main()
