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

    @mock.patch("livemcp.installer.install")
    def test_main_passes_symlink_install_to_installer(self, install):
        server.main(["--install", "--symlink-install"])
        install.assert_called_once_with(use_symlink=True)

    @mock.patch("livemcp.installer.get_install_status", return_value={"installed": True})
    def test_main_prints_install_status(self, get_install_status):
        with mock.patch("sys.stdout", new=io.StringIO()) as stdout:
            server.main(["--install-status"])

        get_install_status.assert_called_once_with()
        self.assertIn('"installed": true', stdout.getvalue().lower())

    @mock.patch(
        "livemcp.server.session.get_validation_readiness",
        return_value={"ready_for_live_validation": True, "selected_device": {"device_name": "Parametric EQ"}},
    )
    def test_main_prints_validation_readiness(self, get_validation_readiness):
        with mock.patch("sys.stdout", new=io.StringIO()) as stdout:
            server.main(["--validation-readiness"])

        get_validation_readiness.assert_called_once_with()
        self.assertIn('"ready_for_live_validation": true', stdout.getvalue().lower())
        self.assertIn("Parametric EQ", stdout.getvalue())

    @mock.patch(
        "livemcp.server.session.confirm_validation_target",
        return_value={"matches": True, "message": "ok"},
    )
    def test_main_prints_validation_target_confirmation(self, confirm_validation_target):
        with mock.patch("sys.stdout", new=io.StringIO()) as stdout:
            server.main(
                [
                    "--confirm-validation-target",
                    "--track-name",
                    "PEQ V2",
                    "--device-name",
                    "Parametric EQ V2",
                ]
            )

        confirm_validation_target.assert_called_once_with(
            track_index=None,
            track_name="PEQ V2",
            device_index=None,
            device_name="Parametric EQ V2",
        )
        self.assertIn('"matches": true', stdout.getvalue().lower())
        self.assertIn("ok", stdout.getvalue())

    @mock.patch("livemcp.installer.install_max_bridge", return_value={"device_path": "/tmp/Bridge.amxd"})
    def test_main_installs_max_bridge(self, install_max_bridge):
        with mock.patch("sys.stdout", new=io.StringIO()) as stdout:
            server.main(["--install-max-bridge"])

        install_max_bridge.assert_called_once_with()
        self.assertIn("/tmp/Bridge.amxd", stdout.getvalue())

    @mock.patch("livemcp.installer.get_max_bridge_status", return_value={"probe_device_installed": True})
    def test_main_prints_max_bridge_status(self, get_max_bridge_status):
        with mock.patch("sys.stdout", new=io.StringIO()) as stdout:
            server.main(["--max-bridge-status"])

        get_max_bridge_status.assert_called_once_with()
        self.assertIn('"probe_device_installed": true', stdout.getvalue().lower())

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

    def test_main_rejects_symlink_install_without_install(self):
        with self.assertRaises(SystemExit) as context:
            with mock.patch("sys.stderr", new=io.StringIO()):
                server.main(["--symlink-install"])

        self.assertEqual(context.exception.code, 2)

    @mock.patch("livemcp.server.sync_docs", return_value={"sources": [{"page_count": 2}]})
    def test_main_syncs_docs(self, sync_docs):
        with mock.patch("sys.stdout", new=io.StringIO()) as stdout:
            server.main(["--sync-docs", "--docs-source", "ableton-live-manual-12"])

        sync_docs.assert_called_once_with(source_ids=["ableton-live-manual-12"])
        self.assertIn('"page_count": 2', stdout.getvalue())

    @mock.patch("livemcp.server.DocsIndex")
    def test_main_prints_docs_status(self, docs_index):
        docs_index.return_value.dumps_status.return_value = '{"total_pages": 10}'

        with mock.patch("sys.stdout", new=io.StringIO()) as stdout:
            server.main(["--docs-status"])

        self.assertIn('"total_pages": 10', stdout.getvalue())

    def test_main_rejects_docs_source_without_sync(self):
        with self.assertRaises(SystemExit) as context:
            with mock.patch("sys.stderr", new=io.StringIO()):
                server.main(["--docs-source", "ableton-live-manual-12"])

        self.assertEqual(context.exception.code, 2)

    def test_main_rejects_validation_target_args_without_flag(self):
        with self.assertRaises(SystemExit) as context:
            with mock.patch("sys.stderr", new=io.StringIO()):
                server.main(["--track-name", "PEQ V2"])

        self.assertEqual(context.exception.code, 2)

    def test_main_rejects_validation_target_flag_without_expected_selector(self):
        with self.assertRaises(SystemExit) as context:
            with mock.patch("sys.stderr", new=io.StringIO()):
                server.main(["--confirm-validation-target"])

        self.assertEqual(context.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
