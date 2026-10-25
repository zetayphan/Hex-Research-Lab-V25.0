# Hex Unified Research Lab V5 — Autonomous Experimental Verification

V5 preserves V4 and adds a **bounded background experimental runner** that advances the actual native engine while recording JSONL per-step metrics and a prediction error for the testable hypothesis that full-engine RGB totals are conserved. Because the native pipeline includes transformative stages, conservation is **not assumed**. No full-engine inverse or structural Jacobian is claimed.

Run `sh start_unified.sh`, then open `http://127.0.0.1:8141/experiments-v5`. The experiment temporarily pauses the ordinary worker to avoid uncontrolled interleaving, then restores its prior running setting. It **modifies the current live engine state**. Runs continue while the server is alive, even when the browser closes. Results are saved under `research_data/experiments_v5/*.jsonl`.

API: `POST /api/v5/start` with `{"steps":30,"delay":0.1}`; `GET /api/v5/status`; `GET /api/v5/runs`; `GET /api/v5/results?id=...`. Step count capped at 10,000. The results endpoint returns up to 1,000 records at once; full history remains in the JSONL file.

Run tests: `python -m unittest discover -s tests -p 'test_experimental_v5.py'`.
