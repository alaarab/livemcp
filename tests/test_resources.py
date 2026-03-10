import json
import sys
import unittest
from pathlib import Path
from unittest import mock

import anyio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp import server


class ResourceTests(unittest.TestCase):
    def test_lists_controller_resources_and_templates(self):
        resources = anyio.run(server.mcp.list_resources)
        templates = anyio.run(server.mcp.list_resource_templates)

        resource_uris = {str(resource.uri) for resource in resources}
        template_uris = {template.uriTemplate for template in templates}

        self.assertIn("live://status", resource_uris)
        self.assertIn("live://session/current", resource_uris)
        self.assertIn("live://selection/track", resource_uris)
        self.assertIn("live://view/current", resource_uris)
        self.assertIn("live://track/{track_index}", template_uris)
        self.assertIn("live://scene/{scene_index}", template_uris)
        self.assertIn("live://device/{track_index}/{device_index}", template_uris)

    @mock.patch("livemcp.resources.session.get_livemcp_status")
    def test_reads_fixed_status_resource(self, get_livemcp_status):
        get_livemcp_status.return_value = {
            "package_version": "1.2.5",
            "client_protocol_version": 2,
            "remote_reachable": True,
            "warnings": [],
        }

        contents = anyio.run(server.mcp.read_resource, "live://status")
        payload = json.loads(contents[0].content)

        self.assertEqual(payload["client_protocol_version"], 2)
        self.assertTrue(payload["remote_reachable"])

    @mock.patch("livemcp.resources._read_track_info")
    def test_reads_track_template_resource(self, read_track_info):
        read_track_info.return_value = {
            "name": "Track 4",
            "type": "midi",
            "devices": [],
        }

        contents = anyio.run(server.mcp.read_resource, "live://track/3")
        payload = json.loads(contents[0].content)

        read_track_info.assert_called_once_with(3)
        self.assertEqual(payload["name"], "Track 4")


if __name__ == "__main__":
    unittest.main()
