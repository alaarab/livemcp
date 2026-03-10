#!/bin/bash
# Install LiveMCP via a symlink for local development on macOS.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$SCRIPT_DIR"
uv run livemcp --install --symlink-install
