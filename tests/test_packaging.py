import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("uv"), "uv is required to build release artifacts")
    def test_wheel_includes_bundled_remote_script(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(
                ["uv", "build", "--wheel", "--out-dir", temp_dir],
                check=True,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            wheel_path = next(Path(temp_dir).glob("livemcp-*.whl"))

            with zipfile.ZipFile(wheel_path) as wheel:
                wheel_files = set(wheel.namelist())

            self.assertIn("livemcp/remote_script/__init__.py", wheel_files)
            self.assertIn("livemcp/remote_script/server.py", wheel_files)
            self.assertIn("livemcp/remote_script/handlers/session.py", wheel_files)
            self.assertIn("livemcp/docs/__init__.py", wheel_files)
            self.assertIn("livemcp/docs/sync.py", wheel_files)
            self.assertIn("livemcp/tools/docs.py", wheel_files)


if __name__ == "__main__":
    unittest.main()
