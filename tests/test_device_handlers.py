"""Remote-script device handlers, tested against Live-object doubles.

The bug this file exists for: ``enable_device`` used to assign
``device.is_enabled``. That attribute is not in the Live Object Model — the LOM
exposes ``Device.is_active`` and it is get-only — so on a real Live device the
assignment silently bound a throwaway Python attribute and nothing was
bypassed. The handler then returned the value it had been ASKED for, so the
tool reported success on a device that was still fully on.

That combination is the worst kind: a no-op that reports success. It survived
because a plain Python double happily accepts ``obj.is_enabled = False`` — so a
naive double reproduces the false success instead of catching it. The doubles
here reject unknown attributes, the way the Live objects do.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from remote_script.LiveMCP.handlers import devices as device_handlers


class FakeParameter:
    def __init__(self, name, value=0.0, minimum=0.0, maximum=1.0):
        self.name = name
        self.value = value
        self.min = minimum
        self.max = maximum


class StrictDevice:
    """A device double that refuses attributes the real LOM does not have.

    Without this, ``device.is_enabled = False`` succeeds against the double and
    the test passes while production silently does nothing.
    """

    _ALLOWED = {"name", "parameters", "class_name", "type", "_initialised"}

    def __init__(self, name, parameters):
        self._initialised = False
        self.name = name
        self.parameters = parameters
        self.class_name = "MxDeviceAudioEffect"
        self.type = 2
        self._initialised = True

    @property
    def is_active(self):
        """Get-only in the LOM, exactly as in Live."""
        return bool(self.parameters[0].value) if self.parameters else True

    def __setattr__(self, key, value):
        if getattr(self, "_initialised", False) and key not in self._ALLOWED:
            raise AttributeError(
                "Live device has no settable attribute {0!r}".format(key))
        object.__setattr__(self, key, value)


class FakeTrack:
    def __init__(self, devices):
        self.devices = devices


class FakeSong:
    def __init__(self, tracks):
        self.tracks = tracks


class FakeControlSurface:
    def __init__(self, song):
        self._song = song

    def song(self):
        return self._song


def _rig(device_on=1.0, extra_params=()):
    params = [FakeParameter("Device On", device_on)] + list(extra_params)
    device = StrictDevice("Ceiling", params)
    return FakeControlSurface(FakeSong([FakeTrack([device])])), device


class EnableDeviceTests(unittest.TestCase):
    def test_disabling_writes_the_device_on_parameter(self):
        surface, device = _rig(device_on=1.0)
        result = device_handlers.enable_device(
            surface, {"track_index": 0, "device_index": 0, "enabled": False})
        self.assertEqual(device.parameters[0].value, 0.0)
        self.assertFalse(result["is_enabled"])
        self.assertFalse(device.is_active)

    def test_enabling_writes_the_device_on_parameter(self):
        surface, device = _rig(device_on=0.0)
        result = device_handlers.enable_device(
            surface, {"track_index": 0, "device_index": 0, "enabled": True})
        self.assertEqual(device.parameters[0].value, 1.0)
        self.assertTrue(result["is_enabled"])

    def test_result_reports_observed_state_not_the_request(self):
        """A no-op must show up as a mismatch, not as success."""
        surface, device = _rig(device_on=1.0)

        class Stuck(FakeParameter):
            @property
            def value(self):
                return 1.0

            @value.setter
            def value(self, _v):
                pass  # a parameter that refuses to move

        device.parameters = [Stuck("Device On", 1.0)]
        result = device_handlers.enable_device(
            surface, {"track_index": 0, "device_index": 0, "enabled": False})
        self.assertTrue(result["is_enabled"])       # what it ACTUALLY is
        self.assertFalse(result["requested"])       # what was asked for
        self.assertNotEqual(result["is_enabled"], result["requested"])

    def test_missing_enabled_is_rejected(self):
        surface, _ = _rig()
        with self.assertRaisesRegex(ValueError, "enabled"):
            device_handlers.enable_device(
                surface, {"track_index": 0, "device_index": 0})

    def test_device_with_no_parameters_raises_rather_than_lying(self):
        device = StrictDevice("Empty", [])
        surface = FakeControlSurface(FakeSong([FakeTrack([device])]))
        with self.assertRaisesRegex(ValueError, "no parameters"):
            device_handlers.enable_device(
                surface, {"track_index": 0, "device_index": 0, "enabled": False})


class SetDeviceParameterTests(unittest.TestCase):
    """parameter_index 0 is Device On — and 0 is falsy, which ate it once."""

    def test_index_zero_is_not_treated_as_missing(self):
        surface, device = _rig(device_on=1.0)
        result = device_handlers.set_device_parameter(
            surface, {"track_index": 0, "device_index": 0,
                      "parameter_index": 0, "value": 0.0})
        self.assertEqual(device.parameters[0].value, 0.0)
        self.assertEqual(result["parameter"], "Device On")

    def test_legacy_param_index_alias_still_works(self):
        surface, device = _rig(device_on=1.0)
        device_handlers.set_device_parameter(
            surface, {"track_index": 0, "device_index": 0,
                      "param_index": 0, "value": 0.0})
        self.assertEqual(device.parameters[0].value, 0.0)

    def test_by_name_when_no_index_is_given(self):
        surface, device = _rig(
            device_on=1.0,
            extra_params=[FakeParameter("Ceiling", -0.3, -12.0, 0.0)])
        device_handlers.set_device_parameter(
            surface, {"track_index": 0, "device_index": 0,
                      "parameter_name": "Ceiling", "value": -6.0})
        self.assertEqual(device.parameters[1].value, -6.0)

    def test_out_of_range_value_is_rejected(self):
        surface, _ = _rig(device_on=1.0)
        with self.assertRaisesRegex(ValueError, "out of range"):
            device_handlers.set_device_parameter(
                surface, {"track_index": 0, "device_index": 0,
                          "parameter_index": 0, "value": 5.0})


class _SwapTrack:
    """A track whose device list supports delete_device, like the LOM."""

    def __init__(self, devices):
        self.devices = devices

    def delete_device(self, index):
        del self.devices[index]


class _SwapView:
    def __init__(self):
        self.selected_track = None
        self.selected_device = None

    def select_device(self, device):
        self.selected_device = device


class _BrowserItem:
    def __init__(self, name):
        self.name = name
        self.uri = "userlibrary:" + name
        self.is_loadable = True
        self.children = []


class _SwapBrowser:
    """Loads over the hotswap target if one is set, else after the selection."""

    def __init__(self, view, honour_hotswap=True, at_end=False):
        self.view = view
        self.honour_hotswap = honour_hotswap
        self.at_end = at_end
        self.hotswap_target = None
        self.user_library = _BrowserItem("User Library")
        self.loaded_with_target = []

    def load_item(self, item):
        track = self.view.selected_track
        new = StrictDevice(item.name.replace(".amxd", ""), [FakeParameter("Device On", 1.0)])
        self.loaded_with_target.append(self.hotswap_target)
        if self.honour_hotswap and self.hotswap_target is not None:
            track.devices[track.devices.index(self.hotswap_target)] = new
        elif self.at_end:
            track.devices.append(new)
        else:
            track.devices.insert(track.devices.index(self.view.selected_device) + 1, new)


class _SwapSong(FakeSong):
    def move_device(self, device, track, index):
        track.devices.remove(device)
        track.devices.insert(index, device)


class _SwapSurface:
    def __init__(self, track, browser, view):
        self._song = _SwapSong([track])
        self._song.view = view
        self._app = type("App", (), {"browser": browser})()

    def song(self):
        return self._song

    def application(self):
        return self._app

    def log_message(self, _msg):
        pass


def _swap_rig(honour_hotswap=True, at_end=False):
    devices = [StrictDevice(n, [FakeParameter("Device On", 1.0)]) for n in ("EQ", "My Gain", "Utility")]
    track = _SwapTrack(devices)
    view = _SwapView()
    browser = _SwapBrowser(view, honour_hotswap, at_end)
    browser.user_library.children = [_BrowserItem("My Gain v2.amxd")]
    return _SwapSurface(track, browser, view), track, browser


class ReplaceDeviceTests(unittest.TestCase):
    def test_hotswap_replaces_in_place_and_clears_the_target(self):
        surface, track, browser = _swap_rig()
        result = device_handlers.replace_device(
            surface, {"track_index": 0, "device_index": 1, "uri": "My Gain v2.amxd"})
        self.assertEqual([d.name for d in track.devices], ["EQ", "My Gain v2", "Utility"])
        self.assertTrue(result["in_place"])
        self.assertEqual(result["replaced_device"], "My Gain")
        self.assertEqual(result["device_name"], "My Gain v2")
        self.assertEqual(browser.loaded_with_target[0].name, "My Gain")
        self.assertIsNone(browser.hotswap_target)

    def test_insert_beside_falls_back_to_deleting_the_old_device(self):
        surface, track, _browser = _swap_rig(honour_hotswap=False)
        result = device_handlers.replace_device(
            surface, {"track_index": 0, "device_index": 1, "uri": "My Gain v2.amxd"})
        self.assertEqual([d.name for d in track.devices], ["EQ", "My Gain v2", "Utility"])
        self.assertFalse(result["in_place"])

    def test_device_appended_at_the_end_is_moved_into_the_slot(self):
        surface, track, _browser = _swap_rig(honour_hotswap=False, at_end=True)
        result = device_handlers.replace_device(
            surface, {"track_index": 0, "device_index": 1, "uri": "My Gain v2.amxd"})
        self.assertEqual([d.name for d in track.devices], ["EQ", "My Gain v2", "Utility"])
        self.assertFalse(result["in_place"])

    def test_unknown_item_leaves_the_chain_untouched(self):
        surface, track, browser = _swap_rig()
        with self.assertRaisesRegex(ValueError, "Browser item not found"):
            device_handlers.replace_device(
                surface, {"track_index": 0, "device_index": 1, "uri": "Nope.amxd"})
        self.assertEqual([d.name for d in track.devices], ["EQ", "My Gain", "Utility"])
        self.assertIsNone(browser.hotswap_target)

    def test_user_library_path_resolves_without_scanning_every_category(self):
        surface, track, _browser = _swap_rig()
        from remote_script.LiveMCP import browser as browser_module
        original = browser_module.find_item_by_uri
        browser_module.find_item_by_uri = lambda *a, **k: self.fail("scanned by URI")
        try:
            device_handlers.replace_device(
                surface, {"track_index": 0, "device_index": 1,
                          "uri": "user_library/My Gain v2.amxd"})
        finally:
            browser_module.find_item_by_uri = original
        self.assertEqual(track.devices[1].name, "My Gain v2")

    def test_missing_uri_is_rejected(self):
        surface, _track, _browser = _swap_rig()
        with self.assertRaisesRegex(ValueError, "uri"):
            device_handlers.replace_device(surface, {"track_index": 0, "device_index": 1})


if __name__ == "__main__":
    unittest.main()
