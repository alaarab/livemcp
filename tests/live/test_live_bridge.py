"""Opt-in integration coverage against a running Ableton LiveMCP bridge."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from livemcp.connection import AbletonConnection


pytestmark = pytest.mark.live_bridge


@pytest.fixture(scope="module")
def live_connection():
    """Connect only when the caller explicitly opts into controlling Live."""
    if os.environ.get("LIVEMCP_RUN_LIVE_TESTS") != "1":
        pytest.skip("set LIVEMCP_RUN_LIVE_TESTS=1 to exercise a running Ableton bridge")

    connection = AbletonConnection()
    try:
        connection.connect()
    except Exception as exc:
        pytest.fail("LiveMCP bridge is unavailable: {0}".format(exc))

    server_info = connection.get_server_info()
    if not server_info:
        pytest.fail("LiveMCP bridge did not return protocol information")

    try:
        yield connection
    finally:
        connection.disconnect()


def test_dialog_control_reaches_real_write_handler_without_pressing_button(live_connection):
    dialog = live_connection.send_command("get_application_dialog", {})

    assert isinstance(dialog["open_dialog_count"], int)
    assert isinstance(dialog["current_dialog_button_count"], int)
    assert isinstance(dialog["current_dialog_message"], str)

    # Equal to button_count is always invalid. This proves the write handler ran
    # across the real bridge without accepting (or dismissing) a live dialog.
    invalid_index = max(0, dialog["current_dialog_button_count"])
    with pytest.raises(RuntimeError, match="No dialog|out of range"):
        live_connection.send_command(
            "press_current_dialog_button",
            {"index": invalid_index},
        )


def test_view_control_switches_and_restores_main_view(live_connection):
    available = live_connection.send_command("get_available_main_views", {})
    available_views = available["available_main_views"]
    assert "Session" in available_views
    assert "Arranger" in available_views

    visibility = {
        name: live_connection.send_command("is_view_visible", {"view_name": name})["visible"]
        for name in ("Session", "Arranger")
    }
    assert any(visibility.values()), "Ableton reported neither Session nor Arrangement as visible"
    original_view = "Session" if visibility["Session"] else "Arranger"
    target_view = "Arranger" if original_view == "Session" else "Session"

    try:
        shown = live_connection.send_command("show_view", {"view_name": target_view})
        focused = live_connection.send_command("focus_view", {"view_name": target_view})
        observed = live_connection.send_command(
            "is_view_visible",
            {"view_name": target_view},
        )

        assert shown == {"view_name": target_view, "visible": True}
        assert focused == {"view_name": target_view, "visible": True}
        assert observed == {"view_name": target_view, "visible": True}
    finally:
        live_connection.send_command("show_view", {"view_name": original_view})
        live_connection.send_command("focus_view", {"view_name": original_view})


def test_device_selection_round_trips_and_restores_selection(live_connection):
    selected = live_connection.send_command("get_selected_device", {}).get("selected_device")
    if selected is None:
        pytest.skip("select a device on a regular track before running the live tier")
    if selected.get("track_scope") != "track":
        pytest.skip("device selection restoration currently requires a regular track")

    track_index = selected["track_index"]
    original_device_index = selected["device_index"]
    if track_index is None or original_device_index is None:
        pytest.skip("selected device did not expose restorable track/device indices")

    track = live_connection.send_command("get_track_info", {"track_index": track_index})
    device_indices = [device["index"] for device in track["devices"]]
    if not device_indices:
        pytest.skip("selected track has no devices")

    target_device_index = next(
        (index for index in device_indices if index != original_device_index),
        original_device_index,
    )

    try:
        result = live_connection.send_command(
            "select_device",
            {"track_index": track_index, "device_index": target_device_index},
        )
        observed = live_connection.send_command("get_selected_device", {})["selected_device"]

        assert result["selected_device"]["track_index"] == track_index
        assert result["selected_device"]["device_index"] == target_device_index
        assert observed["track_index"] == track_index
        assert observed["device_index"] == target_device_index
    finally:
        live_connection.send_command(
            "select_device",
            {"track_index": track_index, "device_index": original_device_index},
        )
