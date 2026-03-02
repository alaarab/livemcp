# LiveMCP

The definitive Model Context Protocol bridge for Ableton Live.

Control Ableton Live from AI assistants like Claude through 33+ tools covering session management, track creation, MIDI editing, device control, mixing, and more.

## Features

- **Session Control** — tempo, transport, playback state
- **Track Management** — create/delete MIDI and audio tracks, return track access
- **Clip Operations** — create clips, add/read MIDI notes, fire/stop clips
- **Device Control** — load instruments/effects, read and set device parameters
- **Mixer** — volume, pan, sends, mute, solo, arm
- **Scene Launch** — fire and create scenes
- **Smart Browser** — 3-strategy loading that finds anything in your User Library, Max for Live devices, and built-in content

## Quick Start

### 1. Install the Remote Script

Clone this repo and run the install script:

```bash
git clone https://github.com/alaarab/livemcp.git
cd livemcp
./scripts/install.sh
```

### 2. Enable in Ableton

1. Open Ableton Live
2. Go to **Preferences > Link, Tempo & MIDI**
3. Under **Control Surface**, select **LiveMCP**
4. You should see "LiveMCP: Server started on port 9877" in the status bar

### 3. Configure Your AI Assistant

Add to your MCP config (`~/.mcp.json` for Claude Code):

```json
{
  "mcpServers": {
    "LiveMCP": {
      "command": "uvx",
      "args": ["livemcp"]
    }
  }
}
```

Or run directly:

```bash
uvx livemcp
```

## Tools

| Category | Tools | Description |
|----------|-------|-------------|
| Session | 4 | Tempo, transport, playback state |
| Tracks | 6 | MIDI/audio track CRUD, return tracks |
| Clips | 10 | Notes, scenes, clip management |
| Devices | 6 | Browser, loading, parameter control |
| Mixer | 7 | Volume, pan, sends, mute, solo, arm |

## Architecture

LiveMCP has two components:

1. **MCP Server** (`src/livemcp/`) — Python package that bridges MCP to Ableton via TCP socket
2. **Remote Script** (`remote_script/LiveMCP/`) — runs inside Ableton, provides the TCP server and direct Live API access

## License

MIT
