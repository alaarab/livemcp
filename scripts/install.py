#!/usr/bin/env python3
"""Cross-platform installer for the LiveMCP remote script into Ableton Live."""

import os
import platform
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
REMOTE_SCRIPT = REPO_DIR / "remote_script" / "LiveMCP"

# Ableton editions to search, in preference order
EDITIONS = ["Live 12 Suite", "Live 12 Standard", "Live 11 Suite"]


def is_wsl():
    """Detect if running inside WSL."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False


def find_ableton_midi_remote_scripts():
    """Return the first existing MIDI Remote Scripts directory."""
    system = platform.system()

    if system == "Darwin":
        for edition in EDITIONS:
            p = Path(f"/Applications/Ableton {edition}.app/Contents/App-Resources/MIDI Remote Scripts")
            if p.is_dir():
                return p

    elif system == "Windows":
        program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        for edition in EDITIONS:
            p = Path(program_data) / "Ableton" / edition / "Resources" / "MIDI Remote Scripts"
            if p.is_dir():
                return p

    elif system == "Linux" and is_wsl():
        for edition in EDITIONS:
            p = Path(f"/mnt/c/ProgramData/Ableton/{edition}/Resources/MIDI Remote Scripts")
            if p.is_dir():
                return p

    return None


def remove_old(target_dir):
    """Remove existing LiveMCP or AbletonMCP installations."""
    livemcp = target_dir / "LiveMCP"
    if livemcp.is_symlink():
        print(f"Removing existing symlink: {livemcp}")
        livemcp.unlink()
    elif livemcp.is_dir():
        print(f"Removing existing directory: {livemcp}")
        shutil.rmtree(livemcp)

    abletonmcp = target_dir / "AbletonMCP"
    if abletonmcp.is_symlink():
        print(f"Removing old AbletonMCP symlink: {abletonmcp}")
        abletonmcp.unlink()
    elif abletonmcp.is_dir():
        print(f"Note: Found AbletonMCP directory. Not removing — delete manually if desired.")


def install(target_dir):
    """Install the remote script into Ableton's MIDI Remote Scripts directory."""
    dest = target_dir / "LiveMCP"

    system = platform.system()
    use_symlink = system == "Darwin"

    if use_symlink:
        os.symlink(REMOTE_SCRIPT, dest)
        print(f"Symlinked: {dest} -> {REMOTE_SCRIPT}")
    else:
        shutil.copytree(REMOTE_SCRIPT, dest)
        count = sum(1 for _ in dest.rglob("*.py"))
        print(f"Copied {count} files to: {dest}")
        if system == "Linux" and is_wsl():
            print("(WSL detected — copied files to Windows path)")


def main():
    if not REMOTE_SCRIPT.is_dir():
        print(f"Error: Remote script not found at {REMOTE_SCRIPT}", file=sys.stderr)
        sys.exit(1)

    target = find_ableton_midi_remote_scripts()
    if target is None:
        system = platform.system()
        print("Error: Could not find Ableton Live installation.", file=sys.stderr)
        if system == "Darwin":
            print("Looked in /Applications/ for Ableton Live 12/11 Suite and Standard.", file=sys.stderr)
        elif system == "Linux" and is_wsl():
            print("Looked in /mnt/c/ProgramData/Ableton/ for Live 12/11.", file=sys.stderr)
        else:
            print("Looked in %PROGRAMDATA%\\Ableton\\ for Live 12/11.", file=sys.stderr)
        sys.exit(1)

    print(f"Found Ableton at: {target}")

    remove_old(target)
    install(target)

    print()
    print("Installation complete!")
    print()
    print("Next steps:")
    print("  1. Restart Ableton Live (or open it)")
    print("  2. Go to Preferences > Link, Tempo & MIDI")
    print("  3. Select 'LiveMCP' as a Control Surface")
    print("  4. You should see 'LiveMCP: Server started on port 9877'")


if __name__ == "__main__":
    main()
