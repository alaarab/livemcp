"""Cross-platform installer for the LiveMCP remote script into Ableton Live."""

import os
import platform
import shutil
import sys
from pathlib import Path

EDITIONS = ["Live 12 Suite", "Live 12 Standard", "Live 11 Suite"]


def _get_remote_script_source():
    """Find the bundled remote script inside the installed package."""
    pkg_dir = Path(__file__).resolve().parent
    # When installed via pip/uvx, files are at livemcp/remote_script/
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


def _find_ableton():
    """Return the first existing MIDI Remote Scripts directory."""
    system = platform.system()

    if system == "Darwin":
        for edition in EDITIONS:
            p = Path(f"/Applications/Ableton {edition}.app/Contents/App-Resources/MIDI Remote Scripts")
            if p.is_dir():
                return p, "macos"

    elif system == "Windows":
        program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        for edition in EDITIONS:
            p = Path(program_data) / "Ableton" / edition / "Resources" / "MIDI Remote Scripts"
            if p.is_dir():
                return p, "windows"

    elif system == "Linux" and _is_wsl():
        for edition in EDITIONS:
            p = Path(f"/mnt/c/ProgramData/Ableton/{edition}/Resources/MIDI Remote Scripts")
            if p.is_dir():
                return p, "wsl"

    return None, None


def _find_all_ableton():
    """Return all existing MIDI Remote Scripts directories."""
    dirs = []
    system = platform.system()

    if system == "Darwin":
        for edition in EDITIONS:
            p = Path(f"/Applications/Ableton {edition}.app/Contents/App-Resources/MIDI Remote Scripts")
            if p.is_dir():
                dirs.append(p)

    elif system == "Windows":
        program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        for edition in EDITIONS:
            p = Path(program_data) / "Ableton" / edition / "Resources" / "MIDI Remote Scripts"
            if p.is_dir():
                dirs.append(p)

    elif system == "Linux" and _is_wsl():
        for edition in EDITIONS:
            p = Path(f"/mnt/c/ProgramData/Ableton/{edition}/Resources/MIDI Remote Scripts")
            if p.is_dir():
                dirs.append(p)

    return dirs


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


def install():
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
    use_symlink = plat == "macos"

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
