# Hex Unified Research Lab V4 — Autonomous Observational Recorder

Preserves V3 dashboards and mathematical verification. Adds a browser-independent server-side recorder and `/autonomous` dashboard. Recording is **off by default**, and can be enabled with the Start recording button. It samples the native engine state every 2 seconds by default and stores JSON Lines in `research_data/observations.jsonl`. The engine must be running to evolve: recording alone does not step it. Closing the browser does not stop server-side recording, but closing Termux or stopping the Python server does.

## Termux
```sh
pkg update && pkg install python clang unzip -y
termux-setup-storage
cd ~/storage/downloads
unzip Hex_Unified_Research_Lab_V4.zip -d ~/hex_unified_v4
cd ~/hex_unified_v4
sh start_unified.sh
```
Open `http://127.0.0.1:8141/autonomous` (or choose `HEX_STUDIO_PORT=8155 sh start_unified.sh` if port is busy).

API: `GET /api/autonomous/status`, `GET /api/autonomous/history?limit=150`, `POST /api/autonomous/config` with JSON `{"enabled":true,"sample_seconds":2}`. Recording is append-only; consider backing up or pruning the JSONL file for long runs. Metrics are observational, not native-engine reversibility proofs or physical dimensional expansion.

Run tests: `python -m unittest discover -s tests -p 'test_autonomous_v4.py'`.
