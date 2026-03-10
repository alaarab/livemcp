import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp.tools import session


class SessionToolTests(unittest.TestCase):
    @mock.patch("livemcp.tools.session.get_connection")
    @mock.patch("livemcp.tools.session.probe_command")
    @mock.patch("livemcp.tools.session.get_install_status")
    def test_get_livemcp_status_combines_local_and_remote_state(
        self,
        get_install_status,
        probe_command,
        get_connection,
    ):
        get_install_status.return_value = {
            "installed": True,
            "needs_install": False,
            "install_mode": "copy",
        }
        probe_command.return_value = {
            "protocol_version": 2,
            "supports_request_ids": True,
            "transport": "tcp-json-lines",
        }
        get_connection.return_value.get_server_info.return_value = {
            "protocol_version": 2,
            "supports_request_ids": True,
            "transport": "tcp-json-lines",
            "legacy_compatibility_mode": False,
        }

        result = json.loads(session.get_livemcp_status())

        self.assertTrue(result["remote_reachable"])
        self.assertEqual(result["remote_info"]["protocol_version"], 2)
        self.assertEqual(result["warnings"], [])


if __name__ == "__main__":
    unittest.main()
