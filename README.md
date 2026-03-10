# LiveMCP

MCP server that exposes Ableton Live's internal Python API to AI assistants. 199 tools across 7 categories: session, clips, tracks, devices, mixer, arrangement, grooves.

[![Tools](https://img.shields.io/badge/Tools-199-blueviolet)](https://github.com/alaarab/livemcp) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB)](https://python.org) [![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## Quick Start

### 1. Install the Remote Script

```bash
uvx livemcp --install
```

That's it. Works on macOS, Windows, and WSL. Auto-detects your Ableton installation and copies the remote script into the right place.

### 2. Enable in Ableton

1. Open **Ableton Live 12**
2. Go to **Preferences > Link, Tempo & MIDI**
3. Under **Control Surface**, select **LiveMCP**
4. Status bar shows: `LiveMCP: Server started on port 9877`

### 3. Add to Your AI Assistant

**Claude Code** (`~/.mcp.json`) or **Claude Desktop** (`claude_desktop_config.json`):

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

### Ableton Lifecycle Helpers (macOS)

Use the packaged helper when Live gets stuck on save, crash-recovery, or restore prompts:

```bash
uv run livemcp --restart-ableton
uv run livemcp --launch-ableton
uv run livemcp --quit-ableton
```

`--restart-ableton` clears `remote_script/__pycache__`, removes Ableton crash-recovery markers
from `~/Library/Preferences/Ableton/Live */`, quits Live, relaunches the detected Ableton app,
accepts common crash/restore dialogs when macOS Accessibility is available, and waits for the
LiveMCP socket on port `9877`.

Config file locations:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

## Tool Reference

| Category | Count |
|----------|------:|
| Session | 72 |
| Clips | 40 |
| Tracks | 32 |
| Devices | 27 |
| Mixer | 14 |
| Arrangement | 9 |
| Grooves | 5 |
| **Total** | **199** |

<details>
<summary>Session Tools (72)</summary>

| Tool | Description |
|------|-------------|
| `get_session_info` | Tempo, time signature, track count, transport state |
| `get_song_time` / `set_song_time` | Current playhead position |
| `get_song_smpte_time` | SMPTE timecode (hours, minutes, seconds, frames) |
| `set_tempo` | Set BPM |
| `start_playback` / `stop_playback` / `continue_playing` | Transport controls |
| `stop_all_clips` | Stop all playing clips |
| `trigger_record` | Toggle session recording |
| `get_record_mode` / `set_record_mode` | Arrangement recording on/off |
| `get_link_state` / `set_ableton_link_enabled` / `set_ableton_link_start_stop_sync_enabled` | Ableton Link and Start/Stop Sync |
| `set_tempo_follower_enabled` | Tempo Follower on/off |
| `get_count_in_state` | Count-in duration and active count-in state |
| `get_session_record_status` / `set_session_record` | Session Record state and status |
| `set_time_signature` | Numerator and denominator |
| `set_loop_region` | Loop on/off, start, length |
| `undo` / `redo` | Undo/redo |
| `tap_tempo` | Tap tempo |
| `set_metronome` | Metronome on/off |
| `set_midi_recording_quantization` | Quantization during recording |
| `capture_midi` | Capture recently played MIDI |
| `capture_and_insert_scene` | Capture playing clips into a new scene |
| `get_cue_points` | List all locators/cue points |
| `create_locator` / `delete_locator` | Locator CRUD |
| `jump_to_cue` / `jump_to_next_cue` / `jump_to_prev_cue` | Navigate cue points |
| `get_selected_track` / `set_selected_track` | Track selection |
| `get_selected_scene` / `set_selected_scene` | Scene selection |
| `get_scene_properties` | Scene tempo and time signature |
| `get_scene_info` | Scene name, color, is_empty, clip count |
| `get_scene_clips` | All clips in a scene across all tracks |
| `set_scene_tempo` / `set_scene_time_signature` | Per-scene tempo and time sig |
| `set_scene_name` / `set_scene_color` | Scene appearance |
| `fire_scene` / `duplicate_scene` / `delete_scene` / `create_scene` | Scene management |
| `set_groove_amount` / `set_scale` | Global groove and scale |
| `get_application_info` | Live version (major, minor, bugfix) |
| `get_application_dialog` / `press_current_dialog_button` | Inspect and control Ableton dialog boxes |
| `get_application_cpu_usage` | Average and peak Live CPU usage |
| `get_available_main_views` / `is_view_visible` | Discover valid view names and visibility |
| `show_view` / `hide_view` / `focus_view` | Control Ableton UI views |
| `toggle_browse` | Toggle browser hot-swap mode |
| `get_session_metadata` | Song time, length, CPU load |
| `get_view_state` | Current view, follow song, draw mode, visible views |
| `get_selected_device` / `select_device` | Read and change selected device |
| `get_selected_parameter` | Inspect the selected parameter |
| `get_selected_chain` | Inspect the selected rack chain |
| `set_follow_song` / `set_draw_mode` | Toggle view options |
| `select_clip_in_detail` | Open clip in Detail View |
| `get_punch_state` / `set_punch_in` / `set_punch_out` | Punch in/out |
| `re_enable_automation` | Re-enable overridden automation |
| `get_session_automation_record` / `set_session_automation_record` | Automation arm |
| `show_message` | Display text in Ableton's status bar |

</details>

<details>
<summary>Clip Tools (40)</summary>

| Tool | Description |
|------|-------------|
| `create_clip` / `create_session_audio_clip` / `delete_clip` / `duplicate_clip` | Clip CRUD |
| `fire_clip` / `stop_clip` | Launch and stop clips |
| `get_clip_properties` | Full clip info (type, length, loop, markers) |
| `set_clip_properties` | Batch set name, color, mute, gain, pitch, loop points |
| `set_clip_name` / `set_clip_color` / `set_clip_muted` | Individual properties |
| `set_clip_loop` | Loop on/off, start, end |
| `set_clip_gain` / `set_clip_pitch` | Audio gain and pitch shift |
| `set_clip_launch_mode` / `set_clip_trigger_quantization` | Launch behavior |
| `set_clip_warp_mode` / `set_clip_warping` | Warping control |
| `set_clip_ram_mode` / `set_clip_velocity_amount` | RAM mode and velocity sensitivity |
| `get_clip_playing_position` | Current playhead within clip |
| `get_clip_fades` / `set_clip_fades` | Audio clip fade in/out lengths |
| `duplicate_clip_loop` / `crop_clip` | Loop duplication and cropping |
| `quantize_clip` | Quantize clip contents |
| `add_notes_to_clip` / `get_notes_from_clip` / `remove_notes_from_clip` / `clear_clip_notes` | Basic MIDI note editing |
| `get_notes_extended` | Notes with probability, velocity deviation, release velocity |
| `add_notes_extended` | Add notes with full MidiNoteSpecification params |
| `modify_notes` | Modify existing notes in place |
| `replace_all_notes` | Atomic note replacement (clear + add in one call) |
| `remove_notes_extended` | Remove notes by pitch/time range |
| `get_clip_envelope` / `insert_clip_envelope_step` / `clear_clip_envelope` / `clear_all_clip_envelopes` | Automation envelopes |

</details>

<details>
<summary>Track Tools (32)</summary>

| Tool | Description |
|------|-------------|
| `get_track_info` / `get_all_tracks_info` | Track details |
| `create_midi_track` / `create_audio_track` / `create_return_track` | Create tracks |
| `delete_track` / `delete_return_track` / `duplicate_track` | Track management |
| `set_track_name` / `set_track_color` | Appearance |
| `set_track_properties` | Batch set name, volume, pan, mute, solo, arm, color |
| `get_track_routing` / `set_track_input_routing` / `set_track_output_routing` | I/O routing |
| `set_track_monitoring` | Monitor modes (auto, in, off) |
| `get_group_info` | Group track children |
| `fold_track` | Fold/unfold group tracks |
| `get_return_tracks` / `get_return_track_sends` / `set_return_track_send` | Return tracks |
| `get_track_freeze_status` | Check if track is frozen |
| `get_track_output_meter` | Real-time output level |
| `get_clip_slot_status` | Playing, recording, triggered state |
| `set_clip_slot_color` | Clip slot color |
| `get_take_lanes` / `create_take_lane` | Take-lane inspection and creation |
| `create_take_lane_midi_clip` / `create_take_lane_audio_clip` | Create clips inside take lanes |

</details>

<details>
<summary>Device Tools (27)</summary>

| Tool | Description |
|------|-------------|
| `get_browser_tree` / `get_browser_items_at_path` | Browse Ableton's content library |
| `load_instrument_or_effect` | Load any instrument or effect by URI, path, or name |
| `load_drum_kit` | Load drum rack presets |
| `load_device_on_master` / `load_device_on_return` | Load to master/return tracks |
| `get_device_parameters` / `set_device_parameter` | Raw parameter values (0.0–1.0) |
| `get_device_display_values` | Human-readable values ("2500 Hz", "-12 dB", "On") |
| `get_master_device_parameters` / `set_master_device_parameter` | Master track devices |
| `get_return_device_parameters` / `set_return_device_parameter` | Return track devices |
| `get_master_track_devices` / `get_return_track_devices` | List devices |
| `get_rack_chains` / `set_chain_mixer_value` | Rack chain contents, activator, pan, volume, sends |
| `get_drum_chains` / `set_drum_chain_property` | Drum-chain note routing and choke settings |
| `get_drum_pads` / `set_drum_pad_mute` / `set_drum_pad_solo` | Drum rack pads |
| `delete_device` / `delete_master_device` / `delete_return_device` | Remove devices |
| `move_device` / `enable_device` | Reorder and enable/disable |

</details>

<details>
<summary>Mixer Tools (14)</summary>

| Tool | Description |
|------|-------------|
| `get_mixer_state` | All tracks: volume, pan, mute, solo, arm, sends |
| `set_track_volume` / `set_track_pan` | Level and panning |
| `set_track_mute` / `set_track_solo` / `set_track_arm` | Mute, solo, arm |
| `set_track_send` | Send levels |
| `get_master_mixer_state` / `set_master_volume` / `set_master_pan` | Master track |
| `set_crossfade_assign` | Crossfader assignment (A/B/none) |
| `get_track_output_meter` | Per-track output metering |
| `get_master_output_meter` | Master output level (L/R) |
| `get_return_track_output_meter` | Return track metering |
| `get_all_track_meters` | All meters in one call |

</details>

<details>
<summary>Arrangement Tools (9)</summary>

| Tool | Description |
|------|-------------|
| `get_arrangement_clips` | All clips on a track's timeline |
| `get_arrangement_length` | Total arrangement length |
| `create_arrangement_midi_clip` | Create MIDI clip at position |
| `create_arrangement_audio_clip` | Place audio file on timeline |
| `duplicate_to_arrangement` | Copy session clip to arrangement |
| `delete_arrangement_clip` | Remove arrangement clip |
| `get_arrangement_overdub` / `set_arrangement_overdub` | Overdub toggle |
| `trigger_back_to_arrangement` | Return to arrangement playback |

</details>

<details>
<summary>Groove Tools (5)</summary>

| Tool | Description |
|------|-------------|
| `get_groove_pool` | List all grooves in the pool |
| `get_groove_properties` | Timing, random, velocity amounts |
| `set_groove_property` | Modify groove parameters |
| `set_clip_groove` | Assign groove to clip |
| `remove_clip_groove` | Clear groove assignment |

</details>

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AI Assistant                         │
│              (Claude, or any MCP client)                 │
└────────────────────────┬────────────────────────────────┘
                         │ MCP Protocol (stdio)
┌────────────────────────▼────────────────────────────────┐
│                   MCP Server                             │
│            src/livemcp/ (FastMCP)                        │
│                                                          │
│   199 tool functions with type hints + docstrings        │
│   7 modules: session, tracks, clips, devices,            │
│              mixer, arrangement, grooves                 │
└────────────────────────┬────────────────────────────────┘
                         │ TCP Socket (localhost:9877)
┌────────────────────────▼────────────────────────────────┐
│              Ableton Remote Script                       │
│         remote_script/LiveMCP/ (Python 3.11)            │
│                                                          │
│   Handler registry: READ (socket thread)                 │
│                      WRITE (main thread via Queue)       │
│   3-strategy browser: URI → path → recursive search      │
└────────────────────────┬────────────────────────────────┘
                         │ Live Object Model
┌────────────────────────▼────────────────────────────────┐
│                  Ableton Live 12                         │
└─────────────────────────────────────────────────────────┘
```

Key design decisions:

- **Thread safety** — Read operations run on the socket thread. Write operations are scheduled on Ableton's main thread via `schedule_message()` + `Queue` to prevent crashes.
- **Handler registry** — `READ_HANDLERS` and `WRITE_HANDLERS` dicts replace if/elif chains. Adding a tool = one handler function + one dict entry.
- **3-strategy browser** — Finds devices by URI match, path navigation, or recursive name search. Handles spaces, special characters, and nested folders automatically.

## Development

```bash
# Clone and set up
git clone https://github.com/alaarab/livemcp.git
cd livemcp

# Install remote script into Ableton
python scripts/install.py

# Run the MCP server locally
uv run livemcp

# Restart Ableton and wait for LiveMCP to come back
uv run livemcp --restart-ableton

# Verify tool count
uv run python -c "from livemcp.server import mcp; print(len(mcp._tool_manager._tools), 'tools')"
```

### Project Structure

```
livemcp/
├── src/livemcp/              # MCP server (pip/uvx installable)
│   ├── server.py             # FastMCP app, registers all tool modules
│   ├── connection.py         # TCP client to remote script
│   └── tools/                # 7 tool modules
│       ├── session.py        # 72 session tools
│       ├── clips.py          # 40 clip tools
│       ├── tracks.py         # 32 track tools
│       ├── devices.py        # 27 device tools
│       ├── mixer.py          # 14 mixer tools
│       ├── arrangement.py    # 9 arrangement tools
│       └── grooves.py        # 5 groove tools
├── remote_script/LiveMCP/    # Ableton MIDI Remote Script
│   ├── __init__.py           # create_instance() entry point
│   ├── server.py             # TCP server + handler dispatch
│   ├── browser.py            # 3-strategy device loading
│   └── handlers/             # 7 handler modules (matching tools/)
└── scripts/
    ├── install.sh            # Wrapper for `uv run livemcp --install`
    ├── uninstall.sh          # Wrapper for `uv run livemcp --uninstall`
    └── restart_ableton.sh    # Wrapper for `uv run livemcp --restart-ableton`
```

## Known Limitations

These are Ableton Live API limitations, not LiveMCP bugs:

| Feature | Status | Notes |
|---------|--------|-------|
| Follow Actions | Not in API | Confirmed by Cycling '74 |
| Stem Separation | Not in API | UI-only feature (Live 12.3+) |
| Track Freeze/Flatten | Read-only | Can check `is_frozen`, cannot trigger freeze |
| Warp Markers | Read-only | Cannot add/move/delete warp markers |
| Automation Envelopes | Limited | Can sample/insert values, cannot create from scratch |
| Group Tracks | Cannot create | Can read group info, cannot create groups |
| Groove Removal | API bug | `clip.groove = None` crashes; raises informative error |

## License

MIT
