# Live bridge integration tests

These tests exercise the real TCP bridge and Ableton Live Object Model. They
cover behavior that socket doubles cannot prove:

- dialog inspection and safe write-handler error dispatch
- showing and focusing Session/Arrangement views
- selecting a device through Live and reading the selection back

## Run

1. Start Ableton Live.
2. Install and enable the LiveMCP MIDI Remote Script.
3. Open a Live Set whose selected regular track has at least one device.
4. Run:

```bash
LIVEMCP_RUN_LIVE_TESTS=1 uv run pytest tests/live -v
```

The explicit environment variable prevents an ordinary unit-test run from
moving the Ableton UI. When enabled, an unreachable bridge is a test failure,
not a skip, so an incorrectly configured validation rig cannot report a false
pass.

## Safety and restoration

The dialog test never presses a valid button. It sends an out-of-range index to
prove that the write handler is reached and its error crosses the real bridge.

The view test records whether Session or Arrangement is visible, exercises the
other view, and restores the original one in a `finally` block. The device test
requires an already selected device on a regular track, selects another device
when one is available (otherwise it reselects the same device), and restores
the original selection in a `finally` block.

These tests target the Ableton remote-script bridge on `127.0.0.1:9877`. They
do not require the optional Max Bridge Hub on port 9881.
