#!/bin/bash
# Install LiveMCP through the packaged CLI helper.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$SCRIPT_DIR"
uv run livemcp --install
