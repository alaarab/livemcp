"""Cross-platform installer for the LiveMCP remote script into Ableton Live."""

import hashlib
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


def _copy_remote_script(source: Path, dest: Path) -> None:
    shutil.copytree(
        source,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )


def _iter_remote_script_files(path: Path):
    if not path.is_dir():
        return []
    return sorted(
        file_path
        for file_path in path.rglob("*")
        if file_path.is_file() and "__pycache__" not in file_path.parts
    )


def _hash_remote_script_tree(path: Path) -> str | None:
    files = _iter_remote_script_files(path)
    if not files:
        return None

    digest = hashlib.sha256()
    for file_path in files:
        digest.update(str(file_path.relative_to(path)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def get_install_status(target_dir: Path | None = None) -> dict:
    """Return install status for the detected Ableton target."""
    source = _get_remote_script_source()
    source_hash = _hash_remote_script_tree(source) if source is not None else None
    source_file_count = len(_iter_remote_script_files(source)) if source is not None else 0

    platform_name = None
    if target_dir is None:
        target_dir, platform_name = _find_ableton()

    dest = target_dir / "LiveMCP" if target_dir is not None else None
    status = {
        "ableton_found": target_dir is not None,
        "target_dir": str(target_dir) if target_dir is not None else None,
        "platform": platform_name,
        "source_found": source is not None,
        "source_path": str(source) if source is not None else None,
        "source_hash": source_hash,
        "source_file_count": source_file_count,
        "dest_path": str(dest) if dest is not None else None,
        "installed": False,
        "install_mode": "missing",
        "installed_hash": None,
        "installed_file_count": 0,
        "in_sync": False,
        "needs_install": True,
    }

    if source is None or dest is None:
        return status

    if dest.is_symlink():
        resolved = dest.resolve()
        status["installed"] = True
        status["install_mode"] = "symlink"
        status["installed_hash"] = _hash_remote_script_tree(resolved)
        status["installed_file_count"] = len(_iter_remote_script_files(resolved))
        status["in_sync"] = resolved == source.resolve()
        status["needs_install"] = not status["in_sync"]
        return status

    if dest.is_dir():
        status["installed"] = True
        status["install_mode"] = "copy"
        status["installed_hash"] = _hash_remote_script_tree(dest)
        status["installed_file_count"] = len(_iter_remote_script_files(dest))
        status["in_sync"] = (
            status["source_hash"] is not None
            and status["installed_hash"] is not None
            and status["source_hash"] == status["installed_hash"]
        )
        status["needs_install"] = not status["in_sync"]
        return status

    return status


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

    if use_symlink is None:
        use_symlink = plat == "macos" and os.environ.get("LIVEMCP_INSTALL_SYMLINK") == "1"
    if use_symlink and plat != "macos":
        print("Error: --symlink-install is only supported on macOS.", file=sys.stderr)
        sys.exit(1)

    print(f"Found Ableton at: {target}")

    _remove_old(target)

    dest = target / "LiveMCP"
    if use_symlink:
        os.symlink(source, dest)
        print(f"Symlinked: {dest} -> {source}")
    else:
        _copy_remote_script(source, dest)
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
