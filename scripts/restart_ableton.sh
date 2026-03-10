#!/bin/bash
# Restart Ableton Live through the packaged livemcp lifecycle helper.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$SCRIPT_DIR"
uv run livemcp --restart-ableton
