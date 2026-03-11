"""LiveMCP — FastMCP server that exposes Ableton Live tools over MCP."""

import argparse

from mcp.server.fastmcp import FastMCP

from .docs import DOC_SOURCES, DocsIndex, sync_docs
from .resources import register_resources
from .tools import session, tracks, clips, devices, mixer, arrangement, grooves, docs

mcp = FastMCP(
    "LiveMCP",
    instructions=(
        "Control and inspect Ableton Live via MCP. Use live:// resources for status, "
        "session, selection, and device state, then use tools to drive transport, "
        "views, tracks, devices, clips, and mixer behavior. LiveMCP is primarily a "
        "controller bridge for Ableton, not a composition agent."
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

    if args.install:
        from .installer import install

        install(use_symlink=args.symlink_install)
    elif args.install_status:
        import json
        from .installer import get_install_status

        print(json.dumps(get_install_status(), indent=2))
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
