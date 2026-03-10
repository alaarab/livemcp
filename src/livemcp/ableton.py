"""macOS Ableton Live app lifecycle helpers."""

from __future__ import annotations

import json
import platform
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path

APP_CANDIDATES = [
    "Ableton Live 12 Suite",
    "Ableton Live 12 Standard",
    "Ableton Live 12 Trial",
    "Ableton Live 11 Suite",
]
PROCESS_NAME = "Live"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
RECV_SIZE = 8192
RECOVERY_FILES = [
    "CrashRecoveryInfo.cfg",
    "CrashDetection.cfg",
    "Undo.lock",
]
QUIT_DIALOG_BUTTONS = ["Don't Save", "Don’t Save", "Discard", "Delete", "No"]
STARTUP_DIALOG_BUTTONS = [
    "Reopen",
    "Restore",
    "Recover",
    "Continue",
    "Open",
    "Yes",
    "OK",
]
FORCE_QUIT_TIMEOUT = 5.0


def _ensure_macos() -> None:
    if platform.system() != "Darwin":
        raise RuntimeError("Ableton app lifecycle helpers are macOS-only")


def find_ableton_app() -> str:
    """Return the preferred Ableton app name installed in /Applications."""
    _ensure_macos()
    applications_dir = Path("/Applications")

    for app_name in APP_CANDIDATES:
        if (applications_dir / f"{app_name}.app").is_dir():
            return app_name

    for app_path in sorted(applications_dir.glob("Ableton Live*.app")):
        return app_path.stem

    raise RuntimeError("Could not find an Ableton Live app in /Applications")


def clear_remote_script_pycache(repo_root: Path | None = None) -> None:
    """Clear remote script __pycache__ directories so Ableton loads fresh code."""
    base_dir = repo_root or Path(__file__).resolve().parents[2]
    remote_script_dir = base_dir / "remote_script"
    if not remote_script_dir.is_dir():
        return

    for cache_dir in remote_script_dir.rglob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)


def _version_key(path: Path) -> tuple[int, ...]:
    match = re.search(r"Live (\d+(?:\.\d+)*)", path.name)
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


def find_ableton_preferences_dir() -> Path | None:
    """Return the newest Ableton preferences directory."""
    prefs_root = Path.home() / "Library" / "Preferences" / "Ableton"
    if not prefs_root.is_dir():
        return None

    candidates = [path for path in prefs_root.iterdir() if path.is_dir() and path.name.startswith("Live ")]
    if not candidates:
        return None

    return max(candidates, key=_version_key)


def clear_recovery_state() -> None:
    """Remove recovery markers so Live starts without restore prompts."""
    prefs_dir = find_ableton_preferences_dir()
    if prefs_dir is None:
        return

    for file_name in RECOVERY_FILES:
        file_path = prefs_dir / file_name
        if file_path.exists():
            file_path.unlink()

    crash_dir = prefs_dir / "Crash"
    if crash_dir.is_dir():
        for child in crash_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)


def _run_osascript(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["osascript", "-e", script],
        check=False,
        capture_output=True,
        text=True,
    )


def _launch_osascript(script: str) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _quote_applescript_list(values: list[str]) -> str:
    escaped = [value.replace('"', '\\"') for value in values]
    return "{" + ", ".join(f'"{value}"' for value in escaped) + "}"


def _click_dialog_button(button_names: list[str]) -> tuple[bool, str]:
    button_list = _quote_applescript_list(button_names)
    script = f"""
on click_first_matching_button(process_name, target_buttons)
    tell application "System Events"
        if not (exists process process_name) then
            return "process_missing"
        end if

        tell process process_name
            set ui_containers to {{}}

            repeat with current_window in windows
                set end of ui_containers to current_window
                try
                    repeat with current_sheet in sheets of current_window
                        set end of ui_containers to current_sheet
                    end repeat
                end try
            end repeat

            repeat with target_button in target_buttons
                repeat with current_container in ui_containers
                    try
                        if exists button (contents of target_button) of current_container then
                            click button (contents of target_button) of current_container
                            return contents of target_button
                        end if
                    end try
                end repeat
            end repeat
        end tell
    end tell

    return "none"
end click_first_matching_button

click_first_matching_button("{PROCESS_NAME}", {button_list})
"""
    result = _run_osascript(script)
    output = (result.stdout or result.stderr or "").strip()
    return result.returncode == 0 and output not in {"", "none", "process_missing"}, output


def _raise_for_accessibility_error(message: str) -> None:
    if "assistive access" in message.lower():
        raise RuntimeError(
            "UI scripting could not inspect Ableton dialogs. Grant Accessibility access "
            "to your terminal/Codex app in System Settings > Privacy & Security > Accessibility."
        )


def wait_for_dialog(button_names: list[str], timeout: float, poll_interval: float = 1.0) -> str | None:
    """Poll for dialog buttons and click the first matching button."""
    deadline = time.time() + timeout
    last_error = ""

    while time.time() < deadline:
        clicked, result = _click_dialog_button(button_names)
        if clicked:
            return result

        last_error = result
        time.sleep(poll_interval)

    _raise_for_accessibility_error(last_error)

    return None


def _dismiss_quit_dialog_via_livemcp(
    timeout: float = 8,
    poll_interval: float = 1.0,
) -> bool:
    """Dismiss Ableton's in-app quit prompt over the LiveMCP socket when available."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            _send_quick_command("press_current_dialog_button", {"index": 0}, timeout=2.0)
            return True
        except RuntimeError as exc:
            if "No dialog is currently open" not in str(exc):
                pass
        except Exception:
            pass

        time.sleep(poll_interval)

    return False


def is_process_running() -> bool:
    """Return whether Ableton's Live process is currently running."""
    result = subprocess.run(
        ["pgrep", "-x", PROCESS_NAME],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _send_quick_command(command_type: str, params: dict, timeout: float = 2.0) -> dict:
    """Send a one-off LiveMCP command with a short timeout.

    This avoids blocking the shared long-timeout connection while Live is quitting.
    """
    payload = json.dumps({"type": command_type, "params": params}).encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect((DEFAULT_HOST, DEFAULT_PORT))
        sock.sendall(payload)

        buffer = b""
        while True:
            chunk = sock.recv(RECV_SIZE)
            if not chunk:
                raise ConnectionError("Remote script closed the connection")
            buffer += chunk
            try:
                response = json.loads(buffer.decode("utf-8"))
                break
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

    if response.get("status") == "error":
        error_msg = response.get("error") or response.get("message", "Unknown error")
        raise RuntimeError(error_msg)

    return response.get("result", {})


def wait_for_process_exit(timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not is_process_running():
            return True
        time.sleep(1)
    return not is_process_running()


def force_kill() -> None:
    subprocess.run(["pkill", "-9", "-x", PROCESS_NAME], check=False, capture_output=True, text=True)


def launch_ableton() -> str:
    """Launch the detected Ableton app."""
    app_name = find_ableton_app()
    subprocess.run(["open", "-a", app_name], check=True)
    return app_name


def quit_ableton(force: bool = True) -> None:
    """Quit Ableton and dismiss save prompts."""
    app_name = find_ableton_app()
    _launch_osascript(f'tell application "{app_name}" to quit')
    time.sleep(0.5)

    exit_timeout = FORCE_QUIT_TIMEOUT if force else 15
    deadline = time.time() + exit_timeout
    last_ui_error = ""
    while time.time() < deadline:
        if not is_process_running():
            return

        if _dismiss_quit_dialog_via_livemcp(timeout=2.5, poll_interval=0.2):
            time.sleep(0.25)
            continue

        try:
            if wait_for_dialog(QUIT_DIALOG_BUTTONS, timeout=0.5, poll_interval=0.1):
                time.sleep(0.25)
                continue
        except RuntimeError as exc:
            last_ui_error = str(exc)

        time.sleep(0.1)

    if not is_process_running():
        return

    if force:
        force_kill()
        time.sleep(2)
        return

    if last_ui_error:
        raise RuntimeError(last_ui_error)


def wait_for_livemcp_socket(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: float = 120,
    poll_interval: float = 2,
    dialog_button_names: list[str] | None = None,
) -> bool:
    """Wait for the remote script socket to accept TCP connections."""
    deadline = time.time() + timeout
    last_dialog_error = ""

    while time.time() < deadline:
        if dialog_button_names:
            _, dialog_result = _click_dialog_button(dialog_button_names)
            last_dialog_error = dialog_result

        with socket.socket() as sock:
            sock.settimeout(2)
            try:
                sock.connect((host, port))
                return True
            except OSError:
                time.sleep(poll_interval)

    _raise_for_accessibility_error(last_dialog_error)
    return False


def restart_ableton() -> str:
    """Restart Ableton with fresh remote-script bytecode and wait for LiveMCP."""
    clear_remote_script_pycache()
    if is_process_running():
        quit_ableton(force=True)

    clear_recovery_state()
    app_name = launch_ableton()
    if not wait_for_livemcp_socket(dialog_button_names=STARTUP_DIALOG_BUTTONS):
        raise RuntimeError(
            f"LiveMCP socket {DEFAULT_HOST}:{DEFAULT_PORT} did not become ready after restart"
        )
    return app_name
