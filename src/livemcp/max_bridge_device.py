"""Helpers for installing a bridge-enabled Max for Live probe device."""

from __future__ import annotations

import json
import os
import platform
import shutil
import struct
import time
from pathlib import Path


BRIDGE_PROBE_DEVICE_NAME = "LiveMCP Bridge Probe"
BRIDGE_DEVICE_FILENAME = f"{BRIDGE_PROBE_DEVICE_NAME}.amxd"
BRIDGE_RUNTIME_FILENAME = "device_bridge.js"
BRIDGE_SERVER_FILENAME = "device_server.js"
BRIDGE_SCHEMA_FILENAME = "schema.json"
DEFAULT_BRIDGE_PORT = 9881
APPVERSION = {
    "major": 8,
    "minor": 6,
    "revision": 5,
    "architecture": "x64",
    "modernui": 1,
}


def _is_wsl() -> bool:
    try:
        with open("/proc/version", "r", encoding="utf-8") as handle:
            return "microsoft" in handle.read().lower()
    except FileNotFoundError:
        return False


def get_user_library_root() -> Path:
    """Return the local Ableton User Library root."""
    env = os.environ.get("LIVEMCP_USER_LIBRARY")
    if env:
        return Path(env).expanduser()

    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Music" / "Ableton" / "User Library"
    if system == "Windows":
        return Path.home() / "Music" / "Ableton" / "User Library"
    if _is_wsl():
        for drive in ("/mnt/d", "/mnt/c"):
            candidate = Path(drive) / "Music" / "Ableton" / "User Library"
            if candidate.is_dir():
                return candidate
    return Path.home() / "Music" / "Ableton" / "User Library"


def get_probe_device_dir(root: Path | None = None) -> Path:
    """Return the folder where the bridge probe device should be written."""
    base = Path(root) if root is not None else get_user_library_root()
    return base / "Presets" / "Audio Effects" / "Max Audio Effect"


def get_probe_device_path(root: Path | None = None) -> Path:
    """Return the full path to the bridge probe device."""
    return get_probe_device_dir(root=root) / BRIDGE_DEVICE_FILENAME


def get_max_bridge_asset_dir() -> Path:
    """Return the packaged max bridge asset directory."""
    pkg_dir = Path(__file__).resolve().parent
    bundled = pkg_dir / "max_bridge"
    if bundled.is_dir():
        return bundled
    return pkg_dir.parent.parent / "max_bridge"


def _newobj(
    object_id: str,
    text: str,
    patching_rect: list[float],
    numinlets: int,
    numoutlets: int,
    outlettype: list[str] | None = None,
    **kwargs,
) -> dict:
    box = {
        "id": object_id,
        "maxclass": "newobj",
        "fontname": "Arial Bold",
        "fontsize": 10.0,
        "numinlets": numinlets,
        "numoutlets": numoutlets,
        "patching_rect": patching_rect,
        "text": text,
    }
    if outlettype:
        box["outlettype"] = outlettype
    box.update(kwargs)
    return {"box": box}


def _comment(
    object_id: str,
    text: str,
    rect: list[float],
    patching_rect: list[float],
    fontsize: float = 10.0,
    fontface: int | None = None,
    textcolor: list[float] | None = None,
    **kwargs,
) -> dict:
    box = {
        "id": object_id,
        "maxclass": "live.comment",
        "numinlets": 1,
        "numoutlets": 0,
        "fontname": "Ableton Sans Medium",
        "fontsize": fontsize,
        "patching_rect": patching_rect,
        "presentation": 1,
        "presentation_rect": rect,
        "text": text,
        "textjustification": 0,
    }
    if fontface is not None:
        box["fontface"] = fontface
    if textcolor is not None:
        box["textcolor"] = textcolor
    box.update(kwargs)
    return {"box": box}


def _panel(
    object_id: str,
    rect: list[float],
    patching_rect: list[float],
    bgcolor: list[float],
    **kwargs,
) -> dict:
    box = {
        "id": object_id,
        "maxclass": "panel",
        "numinlets": 1,
        "numoutlets": 0,
        "patching_rect": patching_rect,
        "presentation": 1,
        "presentation_rect": rect,
        "bgcolor": bgcolor,
        "background": 1,
        "mode": 0,
        "border": 0,
    }
    box.update(kwargs)
    return {"box": box}


def _patchline(source_id: str, source_outlet: int, dest_id: str, dest_inlet: int) -> dict:
    return {
        "patchline": {
            "source": [source_id, source_outlet],
            "destination": [dest_id, dest_inlet],
        }
    }


def _build_probe_patcher_dict(
    name: str = BRIDGE_PROBE_DEVICE_NAME,
    width: int = 430,
    height: int = 190,
) -> dict:
    now = int(time.time())
    boxes = [
        _panel(
            "bridge_bg",
            [0, 0, width, height],
            [0, 0, width, height],
            [0.94, 0.94, 0.95, 1.0],
            varname="bridge_bg",
        ),
        _comment(
            "bridge_title",
            "LiveMCP Bridge Probe",
            [10, 8, 220, 18],
            [10, 8, 220, 18],
            fontsize=13.0,
            fontface=1,
            varname="bridge_title",
        ),
        _comment(
            "bridge_subtitle",
            "Selected-device Max bridge on localhost:9881",
            [10, 28, width - 20, 16],
            [10, 28, width - 20, 16],
            fontsize=10.0,
            textcolor=[0.2, 0.2, 0.2, 0.7],
            varname="bridge_subtitle",
        ),
        _comment(
            "bridge_endpoint",
            "Commands: get_current_patcher, list_boxes, create_box, set_presentation_rect, save_device",
            [10, 50, width - 20, 16],
            [10, 50, width - 20, 16],
            fontsize=9.0,
            textcolor=[0.2, 0.2, 0.2, 0.65],
            varname="bridge_endpoint",
        ),
        _comment(
            "bridge_demo_target",
            "Bridge target: move or restyle this comment through LiveMCP.",
            [10, 88, width - 20, 18],
            [10, 88, width - 20, 18],
            fontsize=11.0,
            varname="bridge_demo_target",
        ),
        _comment(
            "bridge_demo_hint",
            "Typical flow: select this device, call open_selected_device_in_max, inspect boxes, mutate, then save.",
            [10, 112, width - 20, 34],
            [10, 112, width - 20, 34],
            fontsize=9.0,
            textcolor=[0.2, 0.2, 0.2, 0.65],
            linecount=2,
            varname="bridge_demo_hint",
        ),
        _newobj(
            "obj-plugin",
            "plugin~",
            [30, 240, 52, 20],
            numinlets=1,
            numoutlets=2,
            outlettype=["signal", "signal"],
        ),
        _newobj(
            "obj-plugout",
            "plugout~",
            [30, 320, 58, 20],
            numinlets=2,
            numoutlets=0,
        ),
        _newobj(
            "bridge_thisdevice",
            "live.thisdevice",
            [150, 240, 90, 20],
            numinlets=1,
            numoutlets=2,
            outlettype=["bang", ""],
            varname="bridge_thisdevice",
        ),
        _newobj(
            "bridge_defer",
            "deferlow",
            [250, 240, 52, 20],
            numinlets=1,
            numoutlets=1,
            outlettype=[""],
            varname="bridge_defer",
        ),
        _newobj(
            "bridge_runtime",
            f"js {BRIDGE_RUNTIME_FILENAME}",
            [320, 240, 120, 20],
            numinlets=1,
            numoutlets=1,
            outlettype=[""],
            varname="bridge_runtime",
        ),
        _newobj(
            "bridge_server",
            f"node.script {BRIDGE_SERVER_FILENAME} @autostart 1 @watch 0",
            [460, 240, 210, 20],
            numinlets=1,
            numoutlets=1,
            outlettype=[""],
            varname="bridge_server",
        ),
    ]
    lines = [
        _patchline("obj-plugin", 0, "obj-plugout", 0),
        _patchline("obj-plugin", 1, "obj-plugout", 1),
        _patchline("bridge_thisdevice", 0, "bridge_defer", 0),
        _patchline("bridge_defer", 0, "bridge_runtime", 0),
        _patchline("bridge_server", 0, "bridge_runtime", 0),
        _patchline("bridge_runtime", 0, "bridge_server", 0),
    ]
    return {
        "patcher": {
            "fileversion": 1,
            "appversion": APPVERSION,
            "classnamespace": "box",
            "rect": [100.0, 100.0, 900.0, 700.0],
            "openrect": [0.0, 0.0, float(width), float(height)],
            "bglocked": 0,
            "openinpresentation": 1,
            "default_fontface": 0,
            "default_fontname": "Ableton Sans Medium",
            "default_fontsize": 10.0,
            "gridonopen": 1,
            "gridsize": [8.0, 8.0],
            "gridsnaponopen": 1,
            "objectsnaponopen": 1,
            "statusbarvisible": 2,
            "toolbarvisible": 1,
            "lefttoolbarpinned": 0,
            "toptoolbarpinned": 0,
            "righttoolbarpinned": 0,
            "bottomtoolbarpinned": 0,
            "toolbars_unpinned_last_save": 0,
            "tallnewobj": 0,
            "boxanimatetime": 200,
            "enablehscroll": 1,
            "enablevscroll": 1,
            "devicewidth": float(width),
            "description": "",
            "digest": "",
            "tags": "",
            "style": "",
            "subpatcher_template": "",
            "autosave": 0,
            "boxes": boxes,
            "lines": lines,
            "dependency_cache": [
                {"name": BRIDGE_RUNTIME_FILENAME, "type": "TEXT", "implicit": 1},
                {"name": BRIDGE_SERVER_FILENAME, "type": "TEXT", "implicit": 1},
                {"name": BRIDGE_SCHEMA_FILENAME, "type": "JSON", "implicit": 1},
            ],
            "latency": 0,
            "project": {
                "version": 1,
                "creationdate": now,
                "modificationdate": now,
                "viewrect": [0.0, 0.0, 300.0, 500.0],
                "autoorganize": 1,
                "hideprojectwindow": 1,
                "showdependencies": 1,
                "autolocalize": 0,
                "contents": {"patchers": {}},
                "layout": {},
                "searchpath": {},
                "detailsvisible": 0,
                "amxdtype": 0,
                "readonly": 0,
                "devpathtype": 0,
                "devpath": ".",
                "sortmode": 0,
                "viewmode": 0,
            },
            "parameters": {
                "parameterbanks": {
                    "0": {
                        "index": 0,
                        "name": "",
                        "parameters": [],
                    }
                }
            },
        }
    }


def _build_amxd(patcher_dict: dict) -> bytes:
    payload = json.dumps(patcher_dict, indent="\t").encode("utf-8") + b"\n\x00"
    header = b"ampf"
    header += struct.pack("<I", 4)
    header += b"aaaa"
    header += b"meta"
    header += struct.pack("<I", 4)
    header += b"\x00\x00\x00\x00"
    header += b"ptch"
    header += struct.pack("<I", len(payload))
    return header + payload


def write_probe_device(root: Path | None = None) -> dict:
    """Write the bridge probe device and sidecar assets into the User Library."""
    output_dir = get_probe_device_dir(root=root)
    output_dir.mkdir(parents=True, exist_ok=True)

    device_path = output_dir / BRIDGE_DEVICE_FILENAME
    device_path.write_bytes(_build_amxd(_build_probe_patcher_dict()))

    asset_dir = get_max_bridge_asset_dir()
    copied_assets = []
    for filename in (BRIDGE_RUNTIME_FILENAME, BRIDGE_SERVER_FILENAME, BRIDGE_SCHEMA_FILENAME):
        source = asset_dir / filename
        dest = output_dir / filename
        shutil.copyfile(source, dest)
        copied_assets.append(str(dest))

    return {
        "device_path": str(device_path),
        "asset_paths": copied_assets,
        "port": DEFAULT_BRIDGE_PORT,
    }
