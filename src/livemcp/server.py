"""LiveMCP — FastMCP server that exposes Ableton Live tools over MCP."""

import argparse

from mcp.server.fastmcp import FastMCP

from .tools import session, tracks, clips, devices, mixer, arrangement, grooves

mcp = FastMCP(
    "LiveMCP",
    instructions=(
        "Control Ableton Live via MCP. You can manage sessions, tracks, clips, "
        "devices, and mixer settings. Use get_session_info to see the current state, "
        "then explore tracks, create clips, add MIDI notes, load instruments, and more."
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
)

for _fn in _all_tools:
    mcp.tool()(_fn)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LiveMCP MCP server and Ableton helpers")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--install", action="store_true", help="Install the LiveMCP remote script")
    actions.add_argument("--uninstall", action="store_true", help="Uninstall the LiveMCP remote script")
    actions.add_argument("--restart-ableton", action="store_true", help="Restart Ableton and wait for LiveMCP")
    actions.add_argument("--launch-ableton", action="store_true", help="Launch Ableton")
    actions.add_argument("--quit-ableton", action="store_true", help="Quit Ableton")
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
    return parser


def main(argv: list[str] | None = None):
    """Entry point — run the MCP server over stdio, or handle install/uninstall."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.no_force and not args.quit_ableton:
        parser.error("--no-force can only be used with --quit-ableton")
    if args.symlink_install and not args.install:
        parser.error("--symlink-install can only be used with --install")

    if args.install:
        from .installer import install

        install(use_symlink=args.symlink_install)
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
    else:
        mcp.run(transport="stdio")
