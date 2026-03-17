"""LiveMCP — FastMCP server that exposes Ableton Live tools over MCP."""

import argparse

from mcp.server.fastmcp import FastMCP

from .docs import DOC_SOURCES, DocsIndex, sync_docs
from .resources import register_resources
from .tools import session, tracks, clips, devices, mixer, arrangement, grooves, docs
from .tools import max as max_tools

mcp = FastMCP(
    "LiveMCP",
    instructions=(
        "Control and inspect Ableton Live via MCP. Use live:// resources for status, "
        "session, selection, and device state, use max:// resources for Max for Live "
        "bridge state, then use tools to drive transport, views, tracks, devices, "
        "clips, mixer behavior, and native Max patcher inspection when a local Max "
        "bridge session is attached. LiveMCP is primarily a controller bridge for "
        "Ableton, not a composition agent."
    ),
)

def _collect_tools(*tool_groups):
    """Flatten tool groups and fail fast on duplicate MCP tool names."""
    all_tools = []
    seen = {}
    for group in tool_groups:
        for tool in group:
            tool_name = tool.__name__
            if tool_name in seen:
                raise ValueError(
                    "Duplicate tool registration for '{}' from {} and {}".format(
                        tool_name,
                        seen[tool_name].__module__,
                        tool.__module__,
                    )
                )
            seen[tool_name] = tool
            all_tools.append(tool)
    return all_tools


# Register all tool functions from each module
_all_tools = _collect_tools(
    session.TOOLS,
    tracks.TOOLS,
    clips.TOOLS,
    devices.TOOLS,
    mixer.TOOLS,
    arrangement.TOOLS,
    grooves.TOOLS,
    docs.TOOLS,
    max_tools.TOOLS,
)

for _fn in _all_tools:
    mcp.tool()(_fn)

register_resources(mcp)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LiveMCP MCP server and Ableton helpers")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--install", action="store_true", help="Install the LiveMCP remote script")
    actions.add_argument("--uninstall", action="store_true", help="Uninstall the LiveMCP remote script")
    actions.add_argument("--install-status", action="store_true", help="Show remote-script install status")
    actions.add_argument(
        "--validation-readiness",
        action="store_true",
        help="Show whether Ableton is ready for plugin QA: remote reachability, selected track/device, and Max bridge state",
    )
    actions.add_argument(
        "--confirm-validation-target",
        action="store_true",
        help="Confirm that the expected comparison track/device is currently selected before QA screenshots",
    )
    actions.add_argument(
        "--install-max-bridge",
        action="store_true",
        help="Install the LiveMCP Max bridge probe device and sidecar assets into the User Library",
    )
    actions.add_argument(
        "--max-bridge-status",
        action="store_true",
        help="Show the LiveMCP Max bridge probe install status",
    )
    actions.add_argument("--restart-ableton", action="store_true", help="Restart Ableton and wait for LiveMCP")
    actions.add_argument("--launch-ableton", action="store_true", help="Launch Ableton")
    actions.add_argument("--quit-ableton", action="store_true", help="Quit Ableton")
    actions.add_argument(
        "--sync-docs",
        action="store_true",
        help="Sync official Ableton and Cycling '74 docs into the local search index",
    )
    actions.add_argument(
        "--docs-status",
        action="store_true",
        help="Show local docs index status",
    )
    parser.add_argument(
        "--no-force",
        action="store_true",
        help="Do not force-kill Ableton if a quit request stalls; only valid with --quit-ableton",
    )
    parser.add_argument(
        "--symlink-install",
        action="store_true",
        help="Symlink the remote script into Ableton instead of copying it; only valid with --install",
    )
    parser.add_argument(
        "--docs-source",
        action="append",
        choices=sorted(DOC_SOURCES),
        help="Limit docs sync to one or more configured source ids; only valid with --sync-docs",
    )
    parser.add_argument(
        "--track-index",
        type=int,
        help="Expected selected track index; only valid with --confirm-validation-target",
    )
    parser.add_argument(
        "--track-name",
        help="Expected selected track name; only valid with --confirm-validation-target",
    )
    parser.add_argument(
        "--device-index",
        type=int,
        help="Expected selected device index; only valid with --confirm-validation-target",
    )
    parser.add_argument(
        "--device-name",
        help="Expected selected device name; only valid with --confirm-validation-target",
    )
    return parser


def main(argv: list[str] | None = None):
    """Entry point — run the MCP server over stdio, or handle install/uninstall."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.no_force and not args.quit_ableton:
        parser.error("--no-force can only be used with --quit-ableton")
    if args.symlink_install and not args.install:
        parser.error("--symlink-install can only be used with --install")
    if args.docs_source and not args.sync_docs:
        parser.error("--docs-source can only be used with --sync-docs")
    if (
        (args.track_index is not None or args.track_name or args.device_index is not None or args.device_name)
        and not args.confirm_validation_target
    ):
        parser.error(
            "--track-index/--track-name/--device-index/--device-name can only be used with --confirm-validation-target"
        )
    if args.confirm_validation_target and (
        args.track_index is None
        and not args.track_name
        and args.device_index is None
        and not args.device_name
    ):
        parser.error(
            "--confirm-validation-target requires at least one of --track-index, --track-name, --device-index, or --device-name"
        )

    if args.install:
        from .installer import install

        install(use_symlink=args.symlink_install)
    elif args.install_max_bridge:
        import json
        from .installer import install_max_bridge

        print(json.dumps(install_max_bridge(), indent=2))
    elif args.max_bridge_status:
        import json
        from .installer import get_max_bridge_status

        print(json.dumps(get_max_bridge_status(), indent=2))
    elif args.install_status:
        import json
        from .installer import get_install_status

        print(json.dumps(get_install_status(), indent=2))
    elif args.validation_readiness:
        import json

        print(json.dumps(session.get_validation_readiness(), indent=2))
    elif args.confirm_validation_target:
        import json

        print(
            json.dumps(
                session.confirm_validation_target(
                    track_index=args.track_index,
                    track_name=args.track_name,
                    device_index=args.device_index,
                    device_name=args.device_name,
                ),
                indent=2,
            )
        )
    elif args.uninstall:
        from .installer import uninstall

        uninstall()
    elif args.restart_ableton:
        from .ableton import restart_ableton

        app_name = restart_ableton()
        print(f"Restarted {app_name} and confirmed LiveMCP is reachable on port 9877.")
    elif args.launch_ableton:
        from .ableton import launch_ableton

        app_name = launch_ableton()
        print(f"Launched {app_name}.")
    elif args.quit_ableton:
        from .ableton import quit_ableton

        quit_ableton(force=not args.no_force)
        print("Quit Ableton Live.")
    elif args.sync_docs:
        import json

        print(json.dumps(sync_docs(source_ids=args.docs_source), indent=2))
    elif args.docs_status:
        print(DocsIndex().dumps_status())
    else:
        mcp.run(transport="stdio")
