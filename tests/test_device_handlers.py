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


if __name__ == "__main__":
    unittest.main()
