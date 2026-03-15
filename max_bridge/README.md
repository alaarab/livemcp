# LiveMCP Max Bridge Assets

This directory holds the local-only Max for Live bridge runtime shipped with
LiveMCP.

Files:

- `device_bridge.js`: Max `js` runtime for patcher inspection and mutation.
- `device_server.js`: Node for Max TCP server that exposes the bridge on
  `127.0.0.1:9881`.
- `schema.json`: command/capability summary for the packaged bridge.

The intended v1 flow is:

1. Install the bridge probe with `livemcp --install-max-bridge`.
2. Load `LiveMCP Bridge Probe.amxd` in Ableton Live.
3. Select that device.
4. Use `get_selected_max_device`, `get_current_patcher`, `list_patcher_boxes`,
   `create_box`, `set_presentation_rect`, and `save_max_device` through LiveMCP.

Security boundaries:

- The bridge only binds to `127.0.0.1`.
- No command accepts arbitrary code execution.
- Mutations are limited to an allowlisted patcher-editing surface.
