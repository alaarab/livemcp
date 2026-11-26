"""Track handlers against a group track double.

Group (and main/return) tracks have no arm state: reading ``track.arm`` on
one raises in Live, so ``get_track_info`` and ``get_all_tracks_info`` failed
on every set with a group track. Arm is now read only when ``can_be_armed``.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from remote_script.LiveMCP.handlers import tracks as track_handlers


class _Value:
    def __init__(self, value):
        self.value = value


class _GroupTrack:
    name = "Drums"
    mute = False
    solo = False
    color_index = 3
    has_midi_input = False
    has_audio_input = False
    can_be_armed = False
    is_foldable = True
    is_grouped = False
    is_frozen = False
    can_be_frozen = False
    clip_slots = []
    devices = []
    mixer_device = type("Mixer", (), {"volume": _Value(0.85), "panning": _Value(0.0)})()

    @property
    def arm(self):
        raise RuntimeError("Main and Return Tracks have no 'Arm' state!")


class _Song:
    tracks = [_GroupTrack()]


class _Surface:
    def song(self):
        return _Song()


class GroupTrackTests(unittest.TestCase):
    def test_get_track_info_reports_unarmed_instead_of_failing(self):
        info = track_handlers.get_track_info(_Surface(), {"track_index": 0})
        self.assertFalse(info["arm"])
        self.assertEqual(info["devices"], [])

    def test_get_all_tracks_info_includes_group_tracks(self):
        info = track_handlers.get_all_tracks_info(_Surface(), {})
        self.assertEqual(info["track_count"], 1)
        self.assertFalse(info["tracks"][0]["arm"])


if __name__ == "__main__":
    unittest.main()
