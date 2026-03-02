#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
REMOTE_SCRIPT="$REPO_DIR/remote_script/LiveMCP"

# Detect Ableton installation
ABLETON_12="/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts"
ABLETON_12_STD="/Applications/Ableton Live 12 Standard.app/Contents/App-Resources/MIDI Remote Scripts"
ABLETON_11="/Applications/Ableton Live 11 Suite.app/Contents/App-Resources/MIDI Remote Scripts"

if [ -d "$ABLETON_12" ]; then
    TARGET="$ABLETON_12"
elif [ -d "$ABLETON_12_STD" ]; then
    TARGET="$ABLETON_12_STD"
elif [ -d "$ABLETON_11" ]; then
    TARGET="$ABLETON_11"
else
    echo "Error: Could not find Ableton Live installation."
    echo "Looked in:"
    echo "  $ABLETON_12"
    echo "  $ABLETON_12_STD"
    echo "  $ABLETON_11"
    exit 1
fi

echo "Found Ableton at: $TARGET"

# Remove old installations
if [ -L "$TARGET/LiveMCP" ]; then
    echo "Removing existing LiveMCP symlink..."
    rm "$TARGET/LiveMCP"
elif [ -d "$TARGET/LiveMCP" ]; then
    echo "Removing existing LiveMCP directory..."
    rm -rf "$TARGET/LiveMCP"
fi

if [ -L "$TARGET/AbletonMCP" ]; then
    echo "Removing old AbletonMCP symlink..."
    rm "$TARGET/AbletonMCP"
elif [ -d "$TARGET/AbletonMCP" ]; then
    echo "Note: Found AbletonMCP directory (upstream). Not removing — delete manually if desired."
fi

# Create symlink
ln -s "$REMOTE_SCRIPT" "$TARGET/LiveMCP"
echo "Symlinked: $TARGET/LiveMCP -> $REMOTE_SCRIPT"

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Restart Ableton Live (or open it)"
echo "  2. Go to Preferences > Link, Tempo & MIDI"
echo "  3. Select 'LiveMCP' as a Control Surface"
echo "  4. You should see 'LiveMCP: Server started on port 9877'"
