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

# Register all tool functions from each module
_all_tools = (session.TOOLS + tracks.TOOLS + clips.TOOLS + devices.TOOLS + mixer.TOOLS
              + arrangement.TOOLS + grooves.TOOLS)

for _fn in _all_tools:
    mcp.tool()(_fn)


def main():
    """Entry point — run the MCP server over stdio."""
    mcp.run(transport="stdio")
