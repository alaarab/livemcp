#!/usr/bin/env python3
"""Build Custom Saturator .amxd using standard MSP objects (no gen~ codebox)."""
import struct
import json
import os

# Build the main patcher using overdrive~, tanh~, degrade~, clip~ with selector~
patcher = {
    "patcher": {
        "fileversion": 1,
        "appversion": {"major": 8, "minor": 6, "revision": 5, "architecture": "x64", "modernui": 1},
        "classnamespace": "box",
        "rect": [100.0, 100.0, 900.0, 700.0],
        "openrect": [0.0, 0.0, 380.0, 180.0],
        "bglocked": 0,
        "openinpresentation": 1,
        "default_fontsize": 10.0,
        "default_fontface": 0,
        "default_fontname": "Arial Bold",
        "gridonopen": 1,
        "gridsize": [8.0, 8.0],
        "gridsnaponopen": 1,
        "objectsnaponopen": 1,
        "statusbarvisible": 2,
        "toolbarvisible": 1,
        "lefttoolbarpinned": 0,
        "toptoolbarpinned": 0,
        "righttoolbarpinned": 0,
        "bottomtoolbarpinned": 0,
        "toolbars_unpinned_last_save": 0,
        "tallnewobj": 0,
        "boxanimatetime": 500,
        "enablehscroll": 1,
        "enablevscroll": 1,
        "devicewidth": 380.0,
        "description": "Custom Saturator - 4 mode saturation",
        "digest": "",
        "tags": "",
        "style": "",
        "subpatcher_template": "",
        "boxes": [
            # ====== AUDIO I/O ======
            # plugin~ - stereo audio input
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-1", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 2,
                "outlettype": ["signal", "signal"],
                "patching_rect": [30.0, 30.0, 53.0, 20.0],
                "text": "plugin~"
            }},
            # plugout~ - stereo audio output
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-2", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 2,
                "outlettype": ["signal", "signal"],
                "patching_rect": [30.0, 590.0, 57.0, 20.0],
                "text": "plugout~"
            }},

            # ====== DRIVE STAGE - Left ======
            # *~ for drive gain on left channel
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-driveL", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [30.0, 80.0, 40.0, 20.0],
                "text": "*~ 1."
            }},
            # ====== DRIVE STAGE - Right ======
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-driveR", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [150.0, 80.0, 40.0, 20.0],
                "text": "*~ 1."
            }},

            # ====== SATURATION MODES - Left Channel ======
            # Mode 1: tanh~ (soft/tape saturation)
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-tanhL", "maxclass": "newobj",
                "numinlets": 1, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [30.0, 130.0, 40.0, 20.0],
                "text": "tanh~"
            }},
            # Mode 2: overdrive~ (tube-like)
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-odL", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [90.0, 130.0, 73.0, 20.0],
                "text": "overdrive~ 1."
            }},
            # Mode 3: clip~ (hard clip)
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-clipL", "maxclass": "newobj",
                "numinlets": 3, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [180.0, 130.0, 68.0, 20.0],
                "text": "clip~ -0.8 0.8"
            }},
            # Mode 4: degrade~ (bit crush)
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-degL", "maxclass": "newobj",
                "numinlets": 3, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [270.0, 130.0, 75.0, 20.0],
                "text": "degrade~ 0.5 1."
            }},
            # selector~ to pick mode (left)
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-selL", "maxclass": "newobj",
                "numinlets": 5, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [30.0, 180.0, 100.0, 20.0],
                "text": "selector~ 4"
            }},

            # ====== SATURATION MODES - Right Channel ======
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-tanhR", "maxclass": "newobj",
                "numinlets": 1, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [400.0, 130.0, 40.0, 20.0],
                "text": "tanh~"
            }},
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-odR", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [460.0, 130.0, 73.0, 20.0],
                "text": "overdrive~ 1."
            }},
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-clipR", "maxclass": "newobj",
                "numinlets": 3, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [550.0, 130.0, 68.0, 20.0],
                "text": "clip~ -0.8 0.8"
            }},
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-degR", "maxclass": "newobj",
                "numinlets": 3, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [640.0, 130.0, 75.0, 20.0],
                "text": "degrade~ 0.5 1."
            }},
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-selR", "maxclass": "newobj",
                "numinlets": 5, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [400.0, 180.0, 100.0, 20.0],
                "text": "selector~ 4"
            }},

            # ====== TONE FILTER ======
            # onepole~ left
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-toneL", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [30.0, 230.0, 75.0, 20.0],
                "text": "onepole~ 8000"
            }},
            # onepole~ right
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-toneR", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [400.0, 230.0, 75.0, 20.0],
                "text": "onepole~ 8000"
            }},

            # ====== DRY/WET MIX ======
            # Wet gain left
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-wetL", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [30.0, 280.0, 40.0, 20.0],
                "text": "*~ 1."
            }},
            # Dry gain left
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-dryL", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [90.0, 280.0, 40.0, 20.0],
                "text": "*~ 0."
            }},
            # Sum dry+wet left
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-sumL", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [30.0, 320.0, 40.0, 20.0],
                "text": "+~"
            }},
            # Wet gain right
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-wetR", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [400.0, 280.0, 40.0, 20.0],
                "text": "*~ 1."
            }},
            # Dry gain right
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-dryR", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [460.0, 280.0, 40.0, 20.0],
                "text": "*~ 0."
            }},
            # Sum dry+wet right
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-sumR", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [400.0, 320.0, 40.0, 20.0],
                "text": "+~"
            }},

            # ====== OUTPUT GAIN ======
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-outL", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [30.0, 370.0, 40.0, 20.0],
                "text": "*~ 1."
            }},
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-outR", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [400.0, 370.0, 40.0, 20.0],
                "text": "*~ 1."
            }},

            # ====== sig~ converters for control signals ======
            # Drive sig~
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-sigDrive", "maxclass": "newobj",
                "numinlets": 1, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [250.0, 440.0, 35.0, 20.0],
                "text": "sig~"
            }},
            # Tone sig~
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-sigTone", "maxclass": "newobj",
                "numinlets": 1, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [350.0, 440.0, 35.0, 20.0],
                "text": "sig~"
            }},
            # Wet mix sig~
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-sigWet", "maxclass": "newobj",
                "numinlets": 1, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [450.0, 440.0, 35.0, 20.0],
                "text": "sig~"
            }},
            # Dry mix: !- 1. to get (1 - wet)
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-dryCalc", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["float"],
                "patching_rect": [500.0, 440.0, 35.0, 20.0],
                "text": "!- 1."
            }},
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-sigDry", "maxclass": "newobj",
                "numinlets": 1, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [500.0, 470.0, 35.0, 20.0],
                "text": "sig~"
            }},
            # Output sig~
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-sigOut", "maxclass": "newobj",
                "numinlets": 1, "numoutlets": 1,
                "outlettype": ["signal"],
                "patching_rect": [550.0, 440.0, 35.0, 20.0],
                "text": "sig~"
            }},
            # Mode: + 1 to convert 0-3 to 1-4 for selector~
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-modeAdd", "maxclass": "newobj",
                "numinlets": 2, "numoutlets": 1,
                "outlettype": ["int"],
                "patching_rect": [200.0, 440.0, 32.0, 20.0],
                "text": "+ 1"
            }},

            # ====== UI CONTROLS ======
            # Title
            {"box": {
                "id": "obj-title", "maxclass": "live.comment",
                "numinlets": 1, "numoutlets": 0,
                "patching_rect": [600.0, 10.0, 150.0, 18.0],
                "presentation": 1,
                "presentation_rect": [10.0, 6.0, 150.0, 18.0],
                "text": "CUSTOM SATURATOR",
                "textjustification": 0
            }},
            # Mode menu
            {"box": {
                "id": "obj-mode", "maxclass": "live.menu",
                "varname": "Mode",
                "numinlets": 1, "numoutlets": 3,
                "outlettype": ["", "", "float"],
                "parameter_enable": 1,
                "presentation": 1,
                "presentation_rect": [10.0, 26.0, 100.0, 15.0],
                "patching_rect": [200.0, 410.0, 100.0, 15.0],
                "saved_attribute_attributes": {
                    "valueof": {
                        "parameter_longname": "Mode",
                        "parameter_shortname": "Mode",
                        "parameter_type": 2,
                        "parameter_enum": ["Tape", "Tube", "Hard Clip", "Crush"],
                        "parameter_initial_enable": 1,
                        "parameter_initial": [0]
                    }
                }
            }},
            # Drive dial (0-100 -> 0.1-20 via scale)
            {"box": {
                "id": "obj-uiDrive", "maxclass": "live.dial",
                "varname": "Drive",
                "numinlets": 1, "numoutlets": 2,
                "outlettype": ["", "float"],
                "parameter_enable": 1,
                "presentation": 1,
                "presentation_rect": [5.0, 48.0, 55.0, 116.0],
                "patching_rect": [250.0, 380.0, 55.0, 48.0],
                "saved_attribute_attributes": {
                    "valueof": {
                        "parameter_longname": "Drive",
                        "parameter_shortname": "Drive",
                        "parameter_type": 0,
                        "parameter_mmin": 0.0,
                        "parameter_mmax": 100.0,
                        "parameter_initial_enable": 1,
                        "parameter_initial": [50.0],
                        "parameter_unitstyle": 5
                    }
                }
            }},
            # scale for drive: 0-100 -> 0.1-20
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-scaleDrive", "maxclass": "newobj",
                "numinlets": 6, "numoutlets": 1,
                "outlettype": [""],
                "patching_rect": [250.0, 420.0, 90.0, 20.0],
                "text": "scale 0. 100. 0.1 20."
            }},
            # Tone dial (0-100 -> 200-18000 via scale)
            {"box": {
                "id": "obj-uiTone", "maxclass": "live.dial",
                "varname": "Tone",
                "numinlets": 1, "numoutlets": 2,
                "outlettype": ["", "float"],
                "parameter_enable": 1,
                "presentation": 1,
                "presentation_rect": [75.0, 48.0, 55.0, 116.0],
                "patching_rect": [350.0, 380.0, 55.0, 48.0],
                "saved_attribute_attributes": {
                    "valueof": {
                        "parameter_longname": "Tone",
                        "parameter_shortname": "Tone",
                        "parameter_type": 0,
                        "parameter_mmin": 0.0,
                        "parameter_mmax": 100.0,
                        "parameter_initial_enable": 1,
                        "parameter_initial": [100.0],
                        "parameter_unitstyle": 5
                    }
                }
            }},
            # scale for tone: 0-100 -> 200-18000
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-scaleTone", "maxclass": "newobj",
                "numinlets": 6, "numoutlets": 1,
                "outlettype": [""],
                "patching_rect": [350.0, 420.0, 110.0, 20.0],
                "text": "scale 0. 100. 200. 18000."
            }},
            # Mix dial (0-100 -> 0-1 via scale)
            {"box": {
                "id": "obj-uiMix", "maxclass": "live.dial",
                "varname": "Mix",
                "numinlets": 1, "numoutlets": 2,
                "outlettype": ["", "float"],
                "parameter_enable": 1,
                "presentation": 1,
                "presentation_rect": [145.0, 48.0, 55.0, 116.0],
                "patching_rect": [450.0, 380.0, 55.0, 48.0],
                "saved_attribute_attributes": {
                    "valueof": {
                        "parameter_longname": "Mix",
                        "parameter_shortname": "Mix",
                        "parameter_type": 0,
                        "parameter_mmin": 0.0,
                        "parameter_mmax": 100.0,
                        "parameter_initial_enable": 1,
                        "parameter_initial": [100.0],
                        "parameter_unitstyle": 5
                    }
                }
            }},
            # scale for mix: 0-100 -> 0-1
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-scaleMix", "maxclass": "newobj",
                "numinlets": 6, "numoutlets": 1,
                "outlettype": [""],
                "patching_rect": [450.0, 420.0, 85.0, 20.0],
                "text": "scale 0. 100. 0. 1."
            }},
            # Output dial (0-100 -> 0-2 via scale)
            {"box": {
                "id": "obj-uiOut", "maxclass": "live.dial",
                "varname": "Output",
                "numinlets": 1, "numoutlets": 2,
                "outlettype": ["", "float"],
                "parameter_enable": 1,
                "presentation": 1,
                "presentation_rect": [215.0, 48.0, 55.0, 116.0],
                "patching_rect": [550.0, 380.0, 55.0, 48.0],
                "saved_attribute_attributes": {
                    "valueof": {
                        "parameter_longname": "Output",
                        "parameter_shortname": "Output",
                        "parameter_type": 0,
                        "parameter_mmin": 0.0,
                        "parameter_mmax": 100.0,
                        "parameter_initial_enable": 1,
                        "parameter_initial": [50.0],
                        "parameter_unitstyle": 5
                    }
                }
            }},
            # scale for output: 0-100 -> 0-2
            {"box": {
                "fontname": "Arial Bold", "fontsize": 10.0,
                "id": "obj-scaleOut", "maxclass": "newobj",
                "numinlets": 6, "numoutlets": 1,
                "outlettype": [""],
                "patching_rect": [550.0, 420.0, 85.0, 20.0],
                "text": "scale 0. 100. 0. 2."
            }},
        ],
        "lines": [
            # ====== AUDIO SIGNAL PATH ======
            # plugin~ -> drive gain
            {"patchline": {"source": ["obj-1", 0], "destination": ["obj-driveL", 0]}},
            {"patchline": {"source": ["obj-1", 1], "destination": ["obj-driveR", 0]}},

            # plugin~ -> dry path (for mix)
            {"patchline": {"source": ["obj-1", 0], "destination": ["obj-dryL", 0]}},
            {"patchline": {"source": ["obj-1", 1], "destination": ["obj-dryR", 0]}},

            # drive -> all 4 saturation modes (left)
            {"patchline": {"source": ["obj-driveL", 0], "destination": ["obj-tanhL", 0]}},
            {"patchline": {"source": ["obj-driveL", 0], "destination": ["obj-odL", 0]}},
            {"patchline": {"source": ["obj-driveL", 0], "destination": ["obj-clipL", 0]}},
            {"patchline": {"source": ["obj-driveL", 0], "destination": ["obj-degL", 0]}},

            # drive -> all 4 saturation modes (right)
            {"patchline": {"source": ["obj-driveR", 0], "destination": ["obj-tanhR", 0]}},
            {"patchline": {"source": ["obj-driveR", 0], "destination": ["obj-odR", 0]}},
            {"patchline": {"source": ["obj-driveR", 0], "destination": ["obj-clipR", 0]}},
            {"patchline": {"source": ["obj-driveR", 0], "destination": ["obj-degR", 0]}},

            # saturation modes -> selector~ (left) - inlets 1,2,3,4
            {"patchline": {"source": ["obj-tanhL", 0], "destination": ["obj-selL", 1]}},
            {"patchline": {"source": ["obj-odL", 0], "destination": ["obj-selL", 2]}},
            {"patchline": {"source": ["obj-clipL", 0], "destination": ["obj-selL", 3]}},
            {"patchline": {"source": ["obj-degL", 0], "destination": ["obj-selL", 4]}},

            # saturation modes -> selector~ (right)
            {"patchline": {"source": ["obj-tanhR", 0], "destination": ["obj-selR", 1]}},
            {"patchline": {"source": ["obj-odR", 0], "destination": ["obj-selR", 2]}},
            {"patchline": {"source": ["obj-clipR", 0], "destination": ["obj-selR", 3]}},
            {"patchline": {"source": ["obj-degR", 0], "destination": ["obj-selR", 4]}},

            # selector~ -> tone filter
            {"patchline": {"source": ["obj-selL", 0], "destination": ["obj-toneL", 0]}},
            {"patchline": {"source": ["obj-selR", 0], "destination": ["obj-toneR", 0]}},

            # tone -> wet gain
            {"patchline": {"source": ["obj-toneL", 0], "destination": ["obj-wetL", 0]}},
            {"patchline": {"source": ["obj-toneR", 0], "destination": ["obj-wetR", 0]}},

            # wet + dry -> sum
            {"patchline": {"source": ["obj-wetL", 0], "destination": ["obj-sumL", 0]}},
            {"patchline": {"source": ["obj-dryL", 0], "destination": ["obj-sumL", 1]}},
            {"patchline": {"source": ["obj-wetR", 0], "destination": ["obj-sumR", 0]}},
            {"patchline": {"source": ["obj-dryR", 0], "destination": ["obj-sumR", 1]}},

            # sum -> output gain
            {"patchline": {"source": ["obj-sumL", 0], "destination": ["obj-outL", 0]}},
            {"patchline": {"source": ["obj-sumR", 0], "destination": ["obj-outR", 0]}},

            # output gain -> plugout~
            {"patchline": {"source": ["obj-outL", 0], "destination": ["obj-2", 0]}},
            {"patchline": {"source": ["obj-outR", 0], "destination": ["obj-2", 1]}},

            # ====== CONTROL ROUTING ======
            # Mode menu -> + 1 -> selector~ (both L and R)
            {"patchline": {"source": ["obj-mode", 0], "destination": ["obj-modeAdd", 0]}},
            {"patchline": {"source": ["obj-modeAdd", 0], "destination": ["obj-selL", 0]}},
            {"patchline": {"source": ["obj-modeAdd", 0], "destination": ["obj-selR", 0]}},

            # Drive dial -> scale -> sig~ -> *~ drive (both channels)
            {"patchline": {"source": ["obj-uiDrive", 0], "destination": ["obj-scaleDrive", 0]}},
            {"patchline": {"source": ["obj-scaleDrive", 0], "destination": ["obj-sigDrive", 0]}},
            {"patchline": {"source": ["obj-sigDrive", 0], "destination": ["obj-driveL", 1]}},
            {"patchline": {"source": ["obj-sigDrive", 0], "destination": ["obj-driveR", 1]}},

            # Tone dial -> scale -> sig~ -> onepole~ (both channels)
            {"patchline": {"source": ["obj-uiTone", 0], "destination": ["obj-scaleTone", 0]}},
            {"patchline": {"source": ["obj-scaleTone", 0], "destination": ["obj-sigTone", 0]}},
            {"patchline": {"source": ["obj-sigTone", 0], "destination": ["obj-toneL", 1]}},
            {"patchline": {"source": ["obj-sigTone", 0], "destination": ["obj-toneR", 1]}},

            # Mix dial -> scale -> sig~ -> wet gain AND dry calc
            {"patchline": {"source": ["obj-uiMix", 0], "destination": ["obj-scaleMix", 0]}},
            {"patchline": {"source": ["obj-scaleMix", 0], "destination": ["obj-sigWet", 0]}},
            {"patchline": {"source": ["obj-scaleMix", 0], "destination": ["obj-dryCalc", 0]}},
            {"patchline": {"source": ["obj-sigWet", 0], "destination": ["obj-wetL", 1]}},
            {"patchline": {"source": ["obj-sigWet", 0], "destination": ["obj-wetR", 1]}},
            {"patchline": {"source": ["obj-dryCalc", 0], "destination": ["obj-sigDry", 0]}},
            {"patchline": {"source": ["obj-sigDry", 0], "destination": ["obj-dryL", 1]}},
            {"patchline": {"source": ["obj-sigDry", 0], "destination": ["obj-dryR", 1]}},

            # Output dial -> scale -> sig~ -> output gain (both channels)
            {"patchline": {"source": ["obj-uiOut", 0], "destination": ["obj-scaleOut", 0]}},
            {"patchline": {"source": ["obj-scaleOut", 0], "destination": ["obj-sigOut", 0]}},
            {"patchline": {"source": ["obj-sigOut", 0], "destination": ["obj-outL", 1]}},
            {"patchline": {"source": ["obj-sigOut", 0], "destination": ["obj-outR", 1]}},
        ],
        "dependency_cache": [],
        "latency": 0,
        "project": {
            "version": 1,
            "creationdate": 3590052493,
            "modificationdate": 3590052493,
            "viewrect": [0.0, 0.0, 300.0, 500.0],
            "autoorganize": 1,
            "hideprojectwindow": 1,
            "showdependencies": 1,
            "autolocalize": 0,
            "contents": {"patchers": {}},
            "layout": {},
            "searchpath": {},
            "detailsvisible": 0,
            "amxdtype": 1633771873,
            "readonly": 0,
            "devpathtype": 0,
            "devpath": ".",
            "sortmode": 0,
            "viewmode": 0
        },
        "autosave": 0
    }
}

# Serialize JSON with tabs
json_bytes = json.dumps(patcher, indent="\t").encode("utf-8")
json_bytes += b"\n\x00"

# Build binary .amxd container
header = b"ampf"
header += struct.pack("<I", 4)
header += b"aaaa"
header += b"meta"
header += struct.pack("<I", 4)
header += b"\x00\x00\x00\x00"
header += b"ptch"
header += struct.pack("<I", len(json_bytes))

output_path = os.path.expanduser("~/Music/Ableton/User Library/Presets/Audio Effects/Max Audio Effect/Custom Saturator.amxd")
with open(output_path, "wb") as f:
    f.write(header)
    f.write(json_bytes)

print(f"Written {len(header) + len(json_bytes)} bytes to {output_path}")
print(f"Objects: plugin~, plugout~, tanh~, overdrive~, clip~, degrade~, selector~, onepole~, sig~, *~, +~")
print(f"Controls: Mode (4 modes), Drive, Tone, Mix, Output")
