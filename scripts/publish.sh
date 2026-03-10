#!/bin/bash
# Build, test, and publish the current LiveMCP version to PyPI.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$SCRIPT_DIR"

VERSION="$(uv run python - <<'PY'
from livemcp import __version__
print(__version__)
PY
)"

rm -rf dist
uv run python -m unittest discover -s tests -v
uv build
uv publish "$@" "dist/livemcp-${VERSION}.tar.gz" "dist/livemcp-${VERSION}-py3-none-any.whl"
