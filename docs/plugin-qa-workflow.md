# Flagship plugin QA workflow

A repeatable procedure for capturing screenshot evidence during Max for Live
device work — specifically the "flagship versus stock" comparisons (Parametric
EQ V2 / Linear Phase EQ V2 against EQ Eight) that shell and layout passes are
judged on.

**The problem this solves:** a screenshot always looks plausible. It shows *a*
device, rendered correctly, on *a* track. It does not show whether that was the
device you meant, whether it was reloaded after your last build, or whether Live
was even pointing at the track you think it was. Stale selections and stale
device instances have both produced confident, wrong design decisions.

Every step below is enforceable with a tool call, not a habit.

---

## Before you capture anything

### 1. Check the rig is actually ready

```
get_validation_readiness()
```

Returns remote reachability, the currently selected track and device, Max bridge
availability, and suggested next steps. Read it before every session — not once
at the start of the day.

Two failure modes it catches immediately:

- **`remote_reachable: false`** — Ableton is not listening. Nothing else in this
  document will work; every subsequent call fails or returns stale cached data.
- **`max_bridge_reachable: false`** — normal and usually fine. The bridge is only
  needed for native Max patcher inspection, not for loading devices, driving
  parameters, or screenshots. Do not treat this as a blocker for Live-side QA.

### 2. Reload the device from its exact User Library URI

A device already sitting on a track is whatever build was current when it was
*inserted*. Rebuilding and re-freezing does **not** update an existing instance.

Delete the instance and reload it by URI:

```
delete_device(track_index=N, device_index=0)
load_instrument_or_effect(track_index=N,
    uri="query:UserLibrary#Presets:Audio%20Effects:Max%20Audio%20Effect:<Name>.amxd")
```

Loading by URI rather than by name avoids picking up a same-named device from
Factory Packs or `_Archive`. Note the URI is percent-encoded and the path
segments are colon-separated.

> Freeze first. An unfrozen `.amxd` references its `.js` / `.gendsp` /
> `.maxpat` dependencies by filename from the Max search path. That works on
> this machine, so an unfrozen device screenshots fine locally and renders blank
> everywhere else — which is exactly the kind of defect a screenshot will not
> show you.

### 3. Confirm the selection is what you think it is

```
confirm_validation_target(track_name="...", device_name="...")
```

Provide at least one expected selector; names match case-insensitively after
trimming. **Run this immediately before the capture, and again immediately
after any device reload** — reloading changes the selection.

This is the step that makes the evidence trustworthy. Without it you are
asserting from memory that the right thing was on screen.

---

## Capturing

```bash
screencapture -x /path/to/shot.png     # -x = no shutter sound
```

Then crop to the device band. The device chain sits at the bottom of the Live
window; for a 1080-tall window the band is roughly `y = height - 250` to
`height - 30`. Crop and upscale for review — device chrome is small, and
judging typography or spacing from a full-screen shot is not possible.

Take **two** shots per checkpoint:

1. **Structure** — the whole device, for layout, spacing, control grouping.
2. **Material** — a tight crop of one region, for typography, colour, borders.

They answer different questions and a single shot answers neither well.

---

## After capturing — before you use it

Re-run:

```
confirm_validation_target(track_name="...", device_name="...")
```

**Reject the screenshot if the selection does not match, even if the image looks
right.** A plausible-looking image of the wrong device is worse than no image:
it produces a confident decision about something you did not actually inspect.

---

## Storing accepted screenshots

Keep them somewhere durable, not in a scratch directory that gets cleaned.
Name them so they are still meaningful in a month:

```
<device>_<checkpoint>_<track>_<yyyy-mm-dd>[_structure|_material].png
```

e.g. `parametric_eq_shell-pass-2_peqv2_2026-08-01_structure.png`

Without device, track and checkpoint in the filename the archive degrades into
a folder of near-identical dark rectangles.

---

## Same-track comparison pairs

For "before and after" on a shell pass, capture both on the **same track**, at
the same window size, with the same device selected in the chain. A comparison
across two different tracks is not a comparison — track width, chain contents
and the selected-device highlight all change what is drawn.

Procedure:

1. `confirm_validation_target` → capture **before**
2. Rebuild, re-freeze, delete the instance, reload by URI
3. `confirm_validation_target` again (the reload moved the selection)
4. Capture **after**

---

## Known trap: verifying interactive controls

A screenshot **cannot** tell you whether a control works. An inert control
paints exactly like a live one — this is not hypothetical, it is how a batch of
custom v8ui knobs and sliders shipped drag-dead across a whole device fleet.

To prove a control is wired, drive it with real input and read the parameter
back:

```python
# Quartz CGEvents for the gesture...
Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), btn)
Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitLine, 1, +1)
```

```
get_device_parameters(track_index=N, device_index=0)
```

Assert the value moved by the **expected amount**, not merely that it moved —
a wheel handler with an inverted sign still "moves." Reset event flags at the
start of each gesture: a leftover Shift from a previous call silently puts every
subsequent drag into fine mode and looks like a broken control.

---

## Related

- `get_livemcp_status()` — lower-level than `get_validation_readiness`; use it
  when you need install state or protocol versions rather than QA readiness.
- `docs/native-max-for-live-support.md` — the Max bridge, for patcher-level
  inspection rather than Live-side QA.
