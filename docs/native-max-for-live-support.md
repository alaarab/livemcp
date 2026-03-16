# Native Max for Live Support in LiveMCP

Status: implemented in v1 as a selected-device bridge server for bridge-enabled
devices; the older multi-device Bridge Hub concept in this document remains
future-facing.

Scope: add a first-class `max://` namespace and native Max for Live editing path to LiveMCP without making GUI scripting the primary architecture.

## Short architecture summary

LiveMCP keeps a single public MCP surface, the existing package-side FastMCP
server, and the existing package-to-Ableton TCP JSON-lines bridge on
`127.0.0.1:9877`. The implemented v1 Max for Live path adds a second local-only
bridge behind the Ableton remote script:

1. MCP client -> package-side FastMCP (`src/livemcp/`)
2. package-side FastMCP -> Ableton remote script (`remote_script/LiveMCP/`) over the existing TCP bridge
3. Ableton remote script -> selected bridge-enabled Max device over a local TCP JSON-lines bridge on `127.0.0.1:9881`
4. The selected Max device hosts a `node.script` server plus a `js` patcher runtime inside the device itself

The steady-state edit path is native and local:

- LiveMCP identifies the selected device through the Live Object Model.
- The remote script passes the selected-device fingerprint to the device-local bridge.
- The device-local bridge validates that fingerprint against `this_device`.
- The Max bridge runtime uses Max JS APIs such as `this.patcher`, `Maxobj`, `patcher.connect()`, `patcher.remove()`, and `patcher.wind.visible`.
- Editor/view/save actions use native patcher messages equivalent to `thispatcher` commands such as `front`, `presentation 0/1`, and `write`.

GUI scripting is not the main edit architecture. At most, it can remain an optional bootstrap helper for opening a legacy device editor when no native bridge session exists yet.

Current limitation: v1 is intentionally bridge-enabled-device only. The
packaged `LiveMCP Bridge Probe.amxd` in the User Library `Max Audio Effect/_Debug`
folder is the supported reference device. Generic third-party M4L devices
without the packaged bridge runtime remain explicit unsupported/bootstrap-required
cases.

## Current architecture audit

| File | Current role | Max support insertion point |
| --- | --- | --- |
| `src/livemcp/server.py` | Registers all FastMCP tools and resources | Import `tools.max`, register new Max tool group, update server instructions |
| `src/livemcp/resources.py` | Registers `live://` and `docs://` resources | Add `max://status`, `max://selected-device`, and `max://patcher/current` |
| `src/livemcp/connection.py` | Package-side TCP client to Ableton remote script | Preserve existing bridge, but extend capability negotiation and structured-error handling |
| `src/livemcp/protocol.py` | Package-side transport protocol version | Bump transport version when Max capability negotiation becomes part of the remote-script contract |
| `src/livemcp/tools/session.py` | Status, selection, and capability tools | Extend `get_livemcp_info()` / `get_livemcp_status()` with Max bridge capability data and warnings |
| `src/livemcp/tools/` | Package-side tool modules | Add new `max.py` tool module with typed request/response surface |
| `remote_script/LiveMCP/server.py` | Command dispatcher, main-thread scheduling | Inject a `MaxBridgeClient` and route new Max commands through it |
| `remote_script/LiveMCP/handlers/session.py` | Selection and capability handlers | Reuse selected-device logic, add aggregated `max_bridge` capability payloads |
| `remote_script/LiveMCP/handlers/devices.py` | Track/device lookup and device serialization | Reuse device lookup and add Max-device classification helpers/fingerprint generation |
| `remote_script/LiveMCP/handlers/__init__.py` | Merges read/write handler registries | Register `MAX_READ` / `MAX_WRITE` handler sets |
| `remote_script/LiveMCP/protocol.py` | Ableton-side transport protocol version | Keep in sync with package-side transport version |
| `pyproject.toml` | Wheel packaging | Force-include Max bridge assets so the published package can ship the companion bridge bundle |
| `src/livemcp/installer.py` | Ableton remote-script installer | Optionally expose bridge asset location / install status for the Max Bridge Hub |
| `tests/` | Registration, protocol, packaging, CLI tests | Add dedicated Max namespace, protocol, and packaging coverage |
| `README.md` | Product surface and constraints | Document local-only boundaries, unsupported cases, and Max bridge lifecycle |

## Proposed Max namespace

### Resources

| Resource | Shape | Purpose |
| --- | --- | --- |
| `max://status` | fixed | Combined Max bridge reachability, protocol version, install/attach mode, and security warnings |
| `max://selected-device` | fixed | The currently selected Live device, but only populated as a Max device when the selected device is a `MaxDevice` |
| `max://patcher/current` | fixed | Summary of the currently attached patcher session: name, path, dirty state, window visibility, box count, patchline count, and active capabilities |

`max://patcher/current` is intentionally session-scoped rather than path-scoped in v1. It reflects the patcher attached to the currently selected Max device's bridge session.

### Tools

All Max tools should live in a new package-side module `src/livemcp/tools/max.py` and proxy to a new remote-script handler module `remote_script/LiveMCP/handlers/max.py`.

Each mutating Max tool should accept an optional `bridge_session_id`. If omitted, the remote script resolves the current selected Max device and uses its attached bridge session. If the selected device changed after the session was established, the tool must fail with `max/device-mismatch`.

| Tool | Intent | Notes |
| --- | --- | --- |
| `get_selected_max_device` | Return selected Live device metadata if it is a Max device | Includes `supported`, `unsupported_reason`, bridge attach state, and resolved `bridge_session_id` when available |
| `open_selected_device_in_max` | Reveal/focus the selected Max device editor in Max | Primary path: device-local bridge calls `patcher.wind.visible = 1` + `bringtofront()`; if no bridge session exists, return explicit attach/bootstrap error |
| `get_current_patcher` | Read patcher summary for the attached session | Includes `name`, `filepath`, `dirty`, `locked`, `window_visible`, `box_count`, `patchline_count`, `presentation_mode` when known |
| `list_patcher_boxes` | Enumerate boxes in the attached patcher | Returns stable bridge box ids plus `maxclass`, `varname`, `boxtext`, `rect`, `presentation_rect`, `hidden`, `background` |
| `get_box_attrs` | Read a box's object and box attributes | Separate `object_attrs` from `box_attrs` to avoid confusion between `getattr*` and `getboxattr*` |
| `set_box_attrs` | Mutate a box's allowed attributes | Enforce an allowlist and reject unknown or read-only attrs explicitly |
| `create_box` | Create a Max object box in the patcher | Uses `patcher.newdefault(left, top, classname, *args)` plus post-creation attr assignment |
| `create_patchline` | Connect two boxes | Supports visible and hidden connections |
| `delete_box` | Remove a box from the patcher | Uses the bridge's stable box id lookup and `patcher.remove()` |
| `delete_patchline` | Remove a connection between two boxes | Uses `patcher.disconnect()` with explicit outlet/inlet indices |
| `set_presentation_rect` | Update one box's presentation placement | Sets `presentation = 1` and `presentation_rect` for the target box |
| `toggle_presentation_mode` | Toggle the attached patcher between patching and presentation mode | Implement with native patcher messages equivalent to `thispatcher presentation 0/1` |
| `save_max_device` | Save the attached device to its current file path | Use the native patcher save action equivalent to `thispatcher write`; do not accept arbitrary file paths in v1 |

## Max bridge transport design

### Bridge layers

### 1. Existing public transport

Keep the existing package-side JSON-lines transport exactly as the only public bridge used by the MCP server:

- host: `127.0.0.1`
- port: `9877`
- framing: newline-delimited JSON
- request ids: required when both sides advertise protocol v3+

The package side remains unaware of Max internals beyond tool/resource schemas.

### 2. New internal Max bridge transport

Add a second internal JSON-lines transport between the remote script and a Max Bridge Hub:

- host: `127.0.0.1`
- port: `9881`
- framing: newline-delimited JSON
- request ids: always required
- direction: the remote script is the client; Max Bridge Hub is the server

This keeps LiveMCP's package-side architecture unchanged while making the remote script the single coordinator for Live state plus Max state.

### 3. Device-session registration

The Max Bridge Hub manages one or more device-local bridge sessions. Each bridge-enabled Max for Live device loads a hidden helper abstraction that:

- starts when the Max device loads
- computes a device fingerprint from the Live Object Model using `this_device`
- registers itself with the Max Bridge Hub
- exposes patcher CRUD operations through Max JS APIs
- exposes editor/view/save actions through patcher/window APIs and native patcher messages

Recommended registration payload:

```json
{
  "id": 1,
  "type": "register_device_session",
  "params": {
    "bridge_protocol_version": 1,
    "device_fingerprint": {
      "live_path": "live_set tracks 2 devices 5",
      "track_index": 2,
      "device_index": 5,
      "device_name": "My Device",
      "class_name": "MaxDevice"
    },
    "capabilities": {
      "patcher.read": true,
      "patcher.write": true,
      "window.control": true,
      "save": true,
      "presentation.mode": true
    }
  }
}
```

Recommended successful response:

```json
{
  "id": 1,
  "status": "success",
  "result": {
    "bridge_session_id": "max-session-4a9d2f",
    "device_fingerprint": {
      "live_path": "live_set tracks 2 devices 5"
    }
  }
}
```

### 4. Remote-script side proxy contract

The remote script should proxy Max operations instead of exposing a second package-side socket. Proposed internal bridge commands:

- `get_max_bridge_info`
- `find_device_session`
- `show_editor`
- `get_current_patcher`
- `list_boxes`
- `get_box_attrs`
- `set_box_attrs`
- `create_box`
- `connect_boxes`
- `disconnect_boxes`
- `delete_box`
- `set_presentation_rect`
- `set_presentation_mode`
- `save_device`

The remote script resolves the selected Live device first, validates it is a `MaxDevice`, finds a matching device session by fingerprint, and only then proxies to the Max Bridge Hub.

## Capability discovery

Capability discovery should happen in two places:

### `get_livemcp_info`

Extend the existing Ableton-side capability response with an aggregated Max section:

```json
{
  "protocol_version": 3,
  "supports_request_ids": true,
  "transport": "tcp-json-lines",
  "namespaces": ["live", "docs", "max"],
  "max_bridge": {
    "reachable": true,
    "protocol_version": 1,
    "session_mode": "device-session",
    "capabilities": {
      "selected_device": true,
      "patcher_read": true,
      "patcher_write": true,
      "window_control": true,
      "save": true
    }
  }
}
```

If the Max Bridge Hub is down, `reachable` is `false` and `capabilities` are all `false`; LiveMCP stays usable for non-Max commands.

### `get_selected_max_device`

This tool should return the per-device support decision:

- selected device metadata from Live
- `supported: true/false`
- `unsupported_reason`
- attached `bridge_session_id` if available
- per-session capabilities copied from the resolved bridge session

This is the main surface for explicit unsupported cases.

## Error model

LiveMCP currently returns string errors. Max support should add structured errors while preserving string fallback for legacy clients.

Recommended error payload shape:

```json
{
  "status": "error",
  "error": {
    "code": "max/bridge-not-attached",
    "message": "Selected Max device has no active bridge session.",
    "details": {
      "track_index": 2,
      "device_index": 5
    }
  },
  "id": 42
}
```

Package-side connection logic should accept both:

- legacy string: `"Unknown command: ..."`
- structured object: `{"code": "...", "message": "...", "details": {...}}`

Recommended Max error codes:

| Code | Meaning |
| --- | --- |
| `max/not-max-device` | Selected device is not a Max for Live device |
| `max/bridge-unavailable` | Max Bridge Hub is not reachable |
| `max/bridge-not-attached` | Selected Max device has no active bridge session |
| `max/device-mismatch` | Tool supplied a stale `bridge_session_id` for a no-longer-selected device |
| `max/patcher-not-editable` | Session exists but the patcher is read-only / locked against the requested mutation |
| `max/box-not-found` | Requested box id or varname was not found |
| `max/patchline-not-found` | Requested connection does not exist |
| `max/unsupported-attr` | Requested attr is not on the allowlist or not exposed by that Max object |
| `max/save-requires-path` | Device has no current file path and cannot be saved non-interactively |
| `max/bootstrap-required` | Selected device is Max-enabled in Live but no native bridge session exists yet |

## Security rules

Max support must stay local-only and narrowly scoped:

1. All sockets bind to `127.0.0.1` only.
2. No tool accepts arbitrary network destinations.
3. No tool accepts raw JavaScript or arbitrary message strings for execution.
4. `set_box_attrs` uses an explicit allowlist; unknown attrs are rejected.
5. `save_max_device` only saves to the existing device path; no `save as` path input in v1.
6. Mutating tools require a selected Max device plus a matching bridge session.
7. Non-Max devices fail with `max/not-max-device` instead of attempting coercion.
8. README/docs must state that the Max bridge is a local controller surface, not a remote editing daemon.
9. Optional GUI scripting helpers, if retained for bootstrap, must be documented as non-primary fallback behavior.

## Unsupported cases that must be explicit

- Selected device is not a `MaxDevice`
- Selected device is a Max device but has no active bridge session
- A Max device session exists but does not expose write/save/window capabilities
- The selected device changed after the caller cached a `bridge_session_id`
- Save would require interactive `Save As`
- Nested subpatcher editing beyond the top-level patcher session (defer to later phase)

## Phased implementation plan

### Phase 1: namespace + capability plumbing

Goal: land the public Max surface and unsupported-case handling before any patcher mutation work.

Likely files:

- `src/livemcp/server.py`
- `src/livemcp/resources.py`
- `src/livemcp/tools/max.py` (new)
- `src/livemcp/tools/session.py`
- `remote_script/LiveMCP/handlers/max.py` (new)
- `remote_script/LiveMCP/handlers/__init__.py`
- `remote_script/LiveMCP/handlers/session.py`
- `src/livemcp/protocol.py`
- `remote_script/LiveMCP/protocol.py`

Deliverables:

- `max://status`
- `max://selected-device`
- `get_selected_max_device`
- extended `get_livemcp_info`
- structured Max error codes
- explicit unsupported responses for non-M4L devices and missing bridge sessions

Tests/docs:

- `tests/test_max_resources.py`
- `tests/test_max_tools.py`
- `tests/test_registry_guards.py` update for new module registration
- README capability map update

### Phase 2: remote-script to Max Bridge Hub transport

Goal: add the internal bridge client and capability negotiation without exposing mutating tools yet.

Likely files:

- `remote_script/LiveMCP/server.py`
- `remote_script/LiveMCP/max_bridge/client.py` (new)
- `remote_script/LiveMCP/max_bridge/errors.py` (new)
- `tests/test_server_protocol.py`
- `tests/test_connection.py`

Deliverables:

- versioned JSON-lines transport on `127.0.0.1:9881`
- request-id validation
- reconnect-worthy protocol errors on id mismatch
- aggregated bridge info in `get_livemcp_info`

Tests/docs:

- `tests/test_max_bridge_protocol.py`
- docs for protocol versioning and local-only binding

### Phase 3: Max Bridge Hub + read-only patcher inspection

Goal: prove that LiveMCP can inspect real patchers natively before it mutates them.

Likely files:

- `max_bridge/LiveMCP.maxpat` (new)
- `max_bridge/device_bridge.js` (new)
- `max_bridge/transport.js` or `max_bridge/bridge_transport.js` (new)
- `pyproject.toml`
- `tests/test_packaging.py`

Deliverables:

- device-session registration
- `get_current_patcher`
- `list_patcher_boxes`
- `get_box_attrs`
- `open_selected_device_in_max` for attached sessions

Tests/docs:

- packaging test to ensure Max bridge assets ship in the wheel
- docs for running/attaching the bridge
- manual validation checklist for Max editor visibility and session matching

### Phase 4: patcher mutation, presentation, and save

Goal: add controlled write support once read-only inspection is stable.

Likely files:

- `src/livemcp/tools/max.py`
- `remote_script/LiveMCP/handlers/max.py`
- `max_bridge/device_bridge.js`
- `tests/test_max_tools.py`

Deliverables:

- `set_box_attrs`
- `create_box`
- `create_patchline`
- `delete_box`
- `delete_patchline`
- `set_presentation_rect`
- `toggle_presentation_mode`
- `save_max_device`

Tests/docs:

- attr allowlist tests
- box lookup / patchline lookup tests
- protocol tests for mutating commands
- README security section for save behavior and unsupported `save as`

### Phase 5: bootstrap and adoption path

Goal: make bridge adoption practical without making GUI scripting the main edit path.

Likely files:

- `src/livemcp/ableton.py`
- `src/livemcp/installer.py`
- `README.md`
- optional future bridge helper assets

Deliverables:

- documented manual attach flow
- optional bootstrap helper for opening a legacy device editor
- install/status surfacing for bridge assets
- explicit note that bootstrap fallback is optional and not required for bridge-enabled devices

Tests/docs:

- docs-only if bootstrap stays manual
- helper tests only if a package-side bootstrap command is added

## Exact task list

1. Add `src/livemcp/tools/max.py` and register it in `src/livemcp/server.py`.
2. Add `max://status`, `max://selected-device`, and `max://patcher/current` to `src/livemcp/resources.py`.
3. Add `remote_script/LiveMCP/handlers/max.py` and merge it in `remote_script/LiveMCP/handlers/__init__.py`.
4. Extend `remote_script/LiveMCP/handlers/session.py` so `get_livemcp_info()` advertises Max bridge capabilities.
5. Extend `src/livemcp/tools/session.py` so `get_livemcp_status()` warns when the Max bridge is unavailable or not attached.
6. Add `remote_script/LiveMCP/max_bridge/client.py` and wire it into `remote_script/LiveMCP/server.py`.
7. Add bridge protocol/version constants to `src/livemcp/protocol.py` and `remote_script/LiveMCP/protocol.py`.
8. Add packaged Max bridge assets under `max_bridge/` and include them from `pyproject.toml`.
9. Add unit coverage in `tests/test_max_resources.py`, `tests/test_max_tools.py`, and `tests/test_max_bridge_protocol.py`.
10. Update `tests/test_packaging.py` so the wheel must include Max bridge assets.
11. Update `README.md` with the Max namespace, local-only security rules, and unsupported cases.
12. Add a short operator guide for manual bridge attach/bootstrap so the first implementation is usable before full automation exists.

## Risks and open questions

1. Device-session identity is the hardest part. The Max bridge session must emit a fingerprint that the remote script can match reliably to the selected Live `MaxDevice`.
2. Existing third-party M4L devices will not automatically have a device-local bridge session. v1 must say whether the support target is bridge-enabled devices only, or whether a bootstrap attach/inject flow is in scope.
3. `toggle_presentation_mode` is implementable through native patcher messages, but read-back of the current presentation state may need either explicit bridge-side state tracking or an additional verified Max API hook.
4. `save_max_device` should stay overwrite-only in v1. If the patcher has never been saved, LiveMCP must fail explicitly rather than open a file picker.
5. Package compatibility matters: any new structured tool schemas must keep Python 3.10 compatibility on the package side.
6. The Max Bridge Hub introduces a second runtime that must be versioned, packaged, and documented clearly so users do not think the Ableton remote script alone is sufficient.

## Recommended first PR

Start with a read-only, protocol-first PR:

1. Add `src/livemcp/tools/max.py` with `get_selected_max_device`.
2. Add `max://status` and `max://selected-device`.
3. Add `remote_script/LiveMCP/handlers/max.py` with explicit unsupported cases for non-M4L devices and missing bridge sessions.
4. Extend `get_livemcp_info()` and `get_livemcp_status()` with Max bridge capability fields and warnings.
5. Add registration/resource/protocol tests and README/docs updates.

This PR is the right cut because it proves the namespace, error model, and capability negotiation without shipping unsafe patcher mutations before session matching and packaging are settled.
