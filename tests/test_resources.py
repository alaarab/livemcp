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
        max_resource_uris = {uri for uri in resource_uris if uri.startswith("max://")}

        self.assertIn("live://status", resource_uris)
        self.assertIn("live://session/current", resource_uris)
        self.assertIn("live://selection/track", resource_uris)
        self.assertIn("live://view/current", resource_uris)
        self.assertEqual(
            max_resource_uris,
            {"max://status", "max://selected-device", "max://patcher/current"},
        )
        self.assertIn("live://track/{track_index}", template_uris)
        self.assertIn("live://scene/{scene_index}", template_uris)
        self.assertIn("live://device/{track_index}/{device_index}", template_uris)
        self.assertIn("docs://status", resource_uris)
        self.assertIn("docs://chunk/{chunk_id}", template_uris)
        self.assertIn("docs://page/{page_id}", template_uris)

    @mock.patch("livemcp.resources.session.get_livemcp_status")
    def test_reads_fixed_status_resource(self, get_livemcp_status):
        get_livemcp_status.return_value = {
            "package_version": "1.2.5",
            "client_protocol_version": 3,
            "remote_reachable": True,
            "warnings": [],
        }

        contents = anyio.run(server.mcp.read_resource, "live://status")
        payload = json.loads(contents[0].content)

        self.assertEqual(payload["client_protocol_version"], 3)
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

    @mock.patch("livemcp.resources._read_docs_status")
    def test_reads_docs_status_resource(self, read_docs_status):
        read_docs_status.return_value = {
            "docs_root": "/tmp/livemcp-docs",
            "total_pages": 42,
            "total_chunks": 84,
            "configured_sources": [],
        }

        contents = anyio.run(server.mcp.read_resource, "docs://status")
        payload = json.loads(contents[0].content)

        self.assertEqual(payload["total_pages"], 42)

    @mock.patch("livemcp.resources._read_docs_chunk")
    def test_reads_docs_chunk_template_resource(self, read_docs_chunk):
        read_docs_chunk.return_value = {
            "chunk_id": 7,
            "title": "Live API Overview",
            "content": "Properties and functions are exposed through live.object.",
        }

        contents = anyio.run(server.mcp.read_resource, "docs://chunk/7")
        payload = json.loads(contents[0].content)

        read_docs_chunk.assert_called_once_with(7)
        self.assertEqual(payload["chunk_id"], 7)

    @mock.patch("livemcp.resources.session.get_livemcp_status")
    def test_reads_max_status_resource(self, get_livemcp_status):
        get_livemcp_status.return_value = {
            "remote_reachable": True,
            "remote_error": None,
            "max_bridge": {"reachable": False, "port": 9881},
            "warnings": [
                "Max bridge is not currently reachable; Max for Live patcher tools will fail until a local bridge session is available.",
                "Installed LiveMCP remote script is out of sync with the current source; run --install.",
            ],
        }

        contents = anyio.run(server.mcp.read_resource, "max://status")
        payload = json.loads(contents[0].content)

        self.assertEqual(payload["max_bridge"]["port"], 9881)
        self.assertEqual(len(payload["warnings"]), 1)
        self.assertIn("Max bridge", payload["warnings"][0])

    @mock.patch("livemcp.resources.session.get_livemcp_status")
    def test_max_status_resource_filters_only_max_warnings_case_insensitively(self, get_livemcp_status):
        get_livemcp_status.return_value = {
            "remote_reachable": False,
            "remote_error": "socket timeout",
            "max_bridge": {"reachable": False, "port": 9881},
            "warnings": [
                "MAX bridge needs a local attach.",
                "LiveMCP socket is not currently reachable.",
                "max device selection is unavailable.",
            ],
        }

        contents = anyio.run(server.mcp.read_resource, "max://status")
        payload = json.loads(contents[0].content)

        self.assertEqual(payload["remote_error"], "socket timeout")
        self.assertEqual(
            payload["warnings"],
            [
                "MAX bridge needs a local attach.",
                "max device selection is unavailable.",
            ],
        )

    @mock.patch("livemcp.resources.max_tools.get_selected_max_device")
    def test_reads_selected_max_device_resource(self, get_selected_max_device):
        get_selected_max_device.return_value = {
            "supported": True,
            "bridge_session_id": "session-1",
            "selected_device": {"device_name": "Bridge"},
        }

        contents = anyio.run(server.mcp.read_resource, "max://selected-device")
        payload = json.loads(contents[0].content)

        self.assertEqual(payload["bridge_session_id"], "session-1")
        self.assertEqual(payload["selected_device"]["device_name"], "Bridge")

    @mock.patch("livemcp.resources.max_tools.get_current_patcher")
    def test_reads_current_max_patcher_resource(self, get_current_patcher):
        get_current_patcher.return_value = {
            "bridge_session_id": "session-1",
            "name": "bridge.maxpat",
            "box_count": 2,
        }

        contents = anyio.run(server.mcp.read_resource, "max://patcher/current")
        payload = json.loads(contents[0].content)

        self.assertEqual(payload["name"], "bridge.maxpat")
        self.assertEqual(payload["box_count"], 2)


if __name__ == "__main__":
    unittest.main()
