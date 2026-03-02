#!/bin/bash
# Restart Ableton Live with clean remote script cache.
# Handles save dialogs and crash recovery dialogs automatically.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="Ableton Live 12 Suite"
PROCESS_NAME="Ableton Live"
PORT=9877

echo "==> Clearing __pycache__..."
find "$SCRIPT_DIR/remote_script" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "==> Quitting $APP_NAME..."
osascript -e "tell application \"$APP_NAME\" to quit" 2>/dev/null || true

# Dismiss "Save?" dialog
sleep 2
osascript -e "
tell application \"System Events\"
    if exists process \"$PROCESS_NAME\" then
        tell process \"$PROCESS_NAME\"
            if exists window 1 then
                try
                    click button \"Don't Save\" of window 1
                end try
            end if
        end tell
    end if
end tell
" 2>/dev/null || true

# Wait for process exit
echo "==> Waiting for process to exit..."
for i in $(seq 1 15); do
    pgrep -x "$PROCESS_NAME" > /dev/null 2>&1 || break
    sleep 1
done

# Force kill if still hanging
if pgrep -x "$PROCESS_NAME" > /dev/null 2>&1; then
    echo "==> Force killing..."
    pkill -9 -x "$PROCESS_NAME" 2>/dev/null || true
    sleep 2
fi

echo "==> Launching $APP_NAME..."
open -a "$APP_NAME"

# Dismiss "unexpectedly quit" / "Reopen" dialog
echo "==> Checking for crash recovery dialog..."
for i in $(seq 1 15); do
    result=$(osascript -e "
    tell application \"System Events\"
        if exists process \"$PROCESS_NAME\" then
            tell process \"$PROCESS_NAME\"
                if exists window 1 then
                    set btns to name of buttons of window 1
                    if btns contains \"Reopen\" then
                        click button \"Reopen\" of window 1
                        return \"dismissed\"
                    else if btns contains \"OK\" then
                        click button \"OK\" of window 1
                        return \"dismissed\"
                    end if
                end if
            end tell
        end if
    end tell
    return \"none\"
    " 2>/dev/null || echo "none")

    if [ "$result" = "dismissed" ]; then
        echo "    Dismissed dialog."
        break
    fi
    sleep 1
done

# Wait for LiveMCP socket
echo "==> Waiting for LiveMCP socket on port $PORT..."
for i in $(seq 1 60); do
    if python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1', $PORT)); s.close()" 2>/dev/null; then
        echo "==> Connected! LiveMCP is ready."
        exit 0
    fi
    sleep 2
done

echo "==> WARNING: Socket not available after 2 minutes. Check Ableton preferences."
exit 1
