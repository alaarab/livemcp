import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from livemcp.docs import DocsIndex, sync_docs


ABLETON_ROOT = "https://www.ableton.com/en/live-manual/12/"
ABLETON_WARP = "https://www.ableton.com/en/live-manual/12/audio-clips-tempo-and-warping/"


class DocsSyncTests(unittest.TestCase):
    def test_sync_docs_builds_local_index_and_searches_offline(self):
        pages = {
            ABLETON_ROOT: """
                <html>
                    <head><title>Welcome to Live</title></head>
                    <body>
                        <main>
                            <h1>Welcome</h1>
                            <p>Live is a music production environment.</p>
                            <a href="/en/live-manual/12/audio-clips-tempo-and-warping/">Warping</a>
                        </main>
                    </body>
                </html>
            """,
            ABLETON_WARP: """
                <html>
                    <head><title>Audio Clips, Tempo, and Warping</title></head>
                    <body>
                        <main>
                            <h1>Warping</h1>
                            <p>Warp markers let Live lock audio to the session tempo.</p>
                            <p>Use warp markers to align transients and beats.</p>
                        </main>
                    </body>
                </html>
            """,
        }

        def fake_fetch(url: str) -> str:
            return pages[url]

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch("livemcp.docs.sync._fetch_html", side_effect=fake_fetch):
                result = sync_docs(
                    source_ids=["ableton-live-manual-12"],
                    root=root,
                    delay_seconds=0,
                )

            self.assertEqual(result["sources"][0]["page_count"], 2)

            index = DocsIndex(root=root)
            status = index.get_status()
            self.assertEqual(status["total_pages"], 2)
            self.assertGreaterEqual(status["total_chunks"], 2)

            search = index.search("warp markers", source_id="ableton-live-manual-12", limit=3)
            self.assertEqual(search["results"][0]["title"], "Audio Clips, Tempo, and Warping")
            self.assertIn("warp", search["results"][0]["snippet"].lower())
            self.assertIn("markers", search["results"][0]["snippet"].lower())

            chunk = index.get_chunk(search["results"][0]["chunk_id"])
            self.assertIn("session tempo", chunk["content"].lower())
            self.assertTrue(Path(chunk["local_path"]).exists())

    def test_search_tool_serializes_results(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            index = DocsIndex(root=Path(temp_dir))
            index.replace_source(
                "ableton-live-manual-12",
                synced_at="2026-03-11T00:00:00+00:00",
                pages=[
                    {
                        "url": ABLETON_ROOT,
                        "title": "Welcome to Live",
                        "local_path": str(Path(temp_dir) / "raw.html"),
                        "fetched_at": "2026-03-11T00:00:00+00:00",
                        "content_hash": "hash",
                        "text_content": "Live transport and session overview",
                        "chunks": [
                            {
                                "heading": "Welcome",
                                "content": "Live transport and session overview",
                            }
                        ],
                    }
                ],
            )
            with mock.patch("livemcp.tools.docs.DocsIndex", return_value=index):
                from livemcp.tools import docs

                payload = json.loads(docs.search_docs("session overview"))

            self.assertEqual(payload["results"][0]["title"], "Welcome to Live")


if __name__ == "__main__":
    unittest.main()
