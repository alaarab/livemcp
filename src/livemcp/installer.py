"""Cross-platform installer for the LiveMCP remote script into Ableton Live."""

import os
import platform
import re
import shutil
import sys
from pathlib import Path

EDITION_PRIORITY = {
    "Suite": 5,
    "Standard": 4,
    "Intro": 3,
    "Lite": 2,
    "Trial": 1,
}


def _get_remote_script_source():
    """Find the bundled remote script inside the installed package."""
    pkg_dir = Path(__file__).resolve().parent
    # When installed via pip/uvx, wheel data is forced into livemcp/remote_script/
    bundled = pkg_dir / "remote_script"
    if bundled.is_dir():
        return bundled
    # Fallback: running from repo checkout
    repo = pkg_dir.parent.parent
    repo_script = repo / "remote_script" / "LiveMCP"
    if repo_script.is_dir():
        return repo_script
    return None


def _is_wsl():
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False


def _parse_ableton_label(label: str) -> tuple[tuple[int, ...], int, str]:
    match = re.search(r"Live (\d+(?:\.\d+)*) (.+)", label)
    if not match:
        return (0,), 0, label

    version = tuple(int(part) for part in match.group(1).split("."))
    edition = match.group(2).strip()
    return version, EDITION_PRIORITY.get(edition, 0), label


def _sort_key_for_remote_scripts_dir(path: Path) -> tuple[tuple[int, ...], int, str]:
    for ancestor in path.parents:
        if ancestor.suffix == ".app" and ancestor.name.startswith("Ableton Live"):
            return _parse_ableton_label(ancestor.stem)
    return _parse_ableton_label(path.parents[1].name)


def _discover_remote_script_dirs():
    system = platform.system()
    candidates = []

    if system == "Darwin":
        applications_dir = Path("/Applications")
        for app_path in applications_dir.glob("Ableton Live*.app"):
            scripts_dir = app_path / "Contents" / "App-Resources" / "MIDI Remote Scripts"
            if scripts_dir.is_dir():
                candidates.append(scripts_dir)

    elif system == "Windows":
        ableton_root = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Ableton"
        if ableton_root.is_dir():
            for live_dir in ableton_root.glob("Live *"):
                scripts_dir = live_dir / "Resources" / "MIDI Remote Scripts"
                if scripts_dir.is_dir():
                    candidates.append(scripts_dir)

    elif system == "Linux" and _is_wsl():
        ableton_root = Path("/mnt/c/ProgramData/Ableton")
        if ableton_root.is_dir():
            for live_dir in ableton_root.glob("Live *"):
                scripts_dir = live_dir / "Resources" / "MIDI Remote Scripts"
                if scripts_dir.is_dir():
                    candidates.append(scripts_dir)

    return sorted(candidates, key=_sort_key_for_remote_scripts_dir, reverse=True)


def _find_ableton():
    """Return the first existing MIDI Remote Scripts directory."""
    dirs = _discover_remote_script_dirs()
    if not dirs:
        return None, None

    system = platform.system()
    if system == "Darwin":
        platform_name = "macos"
    elif system == "Linux" and _is_wsl():
        platform_name = "wsl"
    else:
        platform_name = system.lower()
    return dirs[0], platform_name


def _find_all_ableton():
    """Return all existing MIDI Remote Scripts directories."""
    return _discover_remote_script_dirs()


def _remove_old(target_dir):
    livemcp = target_dir / "LiveMCP"
    if livemcp.is_symlink():
        livemcp.unlink()
    elif livemcp.is_dir():
        shutil.rmtree(livemcp)

    abletonmcp = target_dir / "AbletonMCP"
    if abletonmcp.is_symlink():
        abletonmcp.unlink()
    elif abletonmcp.is_dir():
        print("Note: Found AbletonMCP directory. Not removing — delete manually if desired.")


def install(use_symlink: bool | None = None):
    source = _get_remote_script_source()
    if source is None:
        print("Error: Could not find the LiveMCP remote script files.", file=sys.stderr)
        sys.exit(1)

    target, plat = _find_ableton()
    if target is None:
        print("Error: Could not find Ableton Live installation.", file=sys.stderr)
        print("Supports macOS, Windows, and WSL.", file=sys.stderr)
        sys.exit(1)

    print(f"Found Ableton at: {target}")

    _remove_old(target)

    dest = target / "LiveMCP"
    if use_symlink is None:
        use_symlink = plat == "macos" and os.environ.get("LIVEMCP_INSTALL_SYMLINK") == "1"
    if use_symlink and plat != "macos":
        print("Error: --symlink-install is only supported on macOS.", file=sys.stderr)
        sys.exit(1)

    if use_symlink:
        os.symlink(source, dest)
        print(f"Symlinked: {dest} -> {source}")
    else:
        shutil.copytree(source, dest)
        count = sum(1 for _ in dest.rglob("*.py"))
        print(f"Copied {count} files to: {dest}")

    print()
    print("Done! Now restart Ableton and select LiveMCP as a Control Surface.")
    print("  Preferences > Link, Tempo & MIDI > Control Surface > LiveMCP")


def uninstall():
    dirs = _find_all_ableton()
    if not dirs:
        print("No Ableton Live installations found.")
        return

    removed = False
    for d in dirs:
        livemcp = d / "LiveMCP"
        if livemcp.is_symlink():
            livemcp.unlink()
            print(f"Removed: {livemcp}")
            removed = True
        elif livemcp.is_dir():
            shutil.rmtree(livemcp)
            print(f"Removed: {livemcp}")
            removed = True

    if removed:
        print("\nUninstall complete. Restart Ableton Live to apply.")
    else:
        print("LiveMCP was not installed in any detected Ableton version.")
