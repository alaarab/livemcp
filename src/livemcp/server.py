"""LiveMCP — FastMCP server that exposes Ableton Live tools over MCP."""

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


def main():
    """Entry point — run the MCP server over stdio, or handle install/uninstall."""
    import sys

    if "--install" in sys.argv:
        from .installer import install
        install()
    elif "--uninstall" in sys.argv:
        from .installer import uninstall
        uninstall()
    elif "--restart-ableton" in sys.argv:
        from .ableton import restart_ableton

        app_name = restart_ableton()
        print(f"Restarted {app_name} and confirmed LiveMCP is reachable on port 9877.")
    elif "--launch-ableton" in sys.argv:
        from .ableton import launch_ableton

        app_name = launch_ableton()
        print(f"Launched {app_name}.")
    elif "--quit-ableton" in sys.argv:
        from .ableton import quit_ableton

        quit_ableton(force="--no-force" not in sys.argv)
        print("Quit Ableton Live.")
    else:
        mcp.run(transport="stdio")
