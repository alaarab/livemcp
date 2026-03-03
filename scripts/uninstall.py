#!/usr/bin/env python3
"""Cross-platform uninstaller for the LiveMCP remote script from Ableton Live."""

import os
import platform
import shutil
import sys
from pathlib import Path

EDITIONS = ["Live 12 Suite", "Live 12 Standard", "Live 11 Suite"]


def is_wsl():
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False


def get_all_midi_remote_scripts_dirs():
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

    elif system == "Linux" and is_wsl():
        for edition in EDITIONS:
            p = Path(f"/mnt/c/ProgramData/Ableton/{edition}/Resources/MIDI Remote Scripts")
            if p.is_dir():
                dirs.append(p)

    return dirs


def main():
    dirs = get_all_midi_remote_scripts_dirs()

    if not dirs:
        print("No Ableton Live installations found.")
        sys.exit(0)

    removed = False
    for d in dirs:
        livemcp = d / "LiveMCP"
        if livemcp.is_symlink():
            livemcp.unlink()
            print(f"Removed symlink: {livemcp}")
            removed = True
        elif livemcp.is_dir():
            shutil.rmtree(livemcp)
            print(f"Removed directory: {livemcp}")
            removed = True

    if removed:
        print("\nUninstall complete. Restart Ableton Live to apply.")
    else:
        print("LiveMCP was not installed in any detected Ableton version.")


if __name__ == "__main__":
    main()
