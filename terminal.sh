#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
export HEX_STUDIO_PORT="${HEX_STUDIO_PORT:-8141}"
exec python3 hex_terminal.py
