#!/usr/bin/env bash
# Wrapper script for launchd — loads .env and runs the daemon
set -euo pipefail

cd /Users/nicoloboschi/dev/seo-booster

# Load .env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

exec /Users/nicoloboschi/.local/bin/uv run seo-booster run
