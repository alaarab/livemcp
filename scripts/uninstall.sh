#!/bin/bash
set -e

ABLETON_12="/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts"
ABLETON_12_STD="/Applications/Ableton Live 12 Standard.app/Contents/App-Resources/MIDI Remote Scripts"
ABLETON_11="/Applications/Ableton Live 11 Suite.app/Contents/App-Resources/MIDI Remote Scripts"

for DIR in "$ABLETON_12" "$ABLETON_12_STD" "$ABLETON_11"; do
    if [ -L "$DIR/LiveMCP" ]; then
        rm "$DIR/LiveMCP"
        echo "Removed symlink: $DIR/LiveMCP"
    elif [ -d "$DIR/LiveMCP" ]; then
        rm -rf "$DIR/LiveMCP"
        echo "Removed directory: $DIR/LiveMCP"
    fi
done

echo "LiveMCP uninstalled."
