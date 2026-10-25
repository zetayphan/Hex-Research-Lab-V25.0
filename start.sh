#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
mkdir -p build diagnostics
if command -v clang >/dev/null 2>&1; then CC=${CC:-clang}; elif command -v cc >/dev/null 2>&1; then CC=${CC:-cc}; else echo 'Missing C compiler. In Termux: pkg install clang' >&2; exit 1; fi
command -v python3 >/dev/null 2>&1 || { echo 'Missing Python 3. In Termux: pkg install python' >&2; exit 1; }
"$CC" -O2 -std=c11 -shared -fPIC src/engine.c -o build/libhexstudio.so
"$CC" -O2 -std=c11 -shared -fPIC src/terminal_native.c -o build/libhexterminal.so
# Rebuild both shared libraries on this host; never load bundled foreign-architecture binaries.
echo "Native libraries compiled for current device."
echo "Starting Hex Studio Pro X V10.3 on port ${HEX_STUDIO_PORT:-8141}..."
exec python3 -u src/server.py --port "${HEX_STUDIO_PORT:-8141}" "$@"
