# Hex Unified Research Lab V6 — Mathematical Pattern Discovery

V6 adds descriptive pattern analysis and cross-run comparisons over V5 native experiment JSONL records. The V5 engine, dashboard, and APIs remain intact.

Start: `sh start_unified.sh`; open `http://127.0.0.1:8141/discovery-v6`. First create runs at `/experiments-v5`, then select one or more runs and click Analyze.

API: `GET /api/v6/discovery?id=RUN_ID` (repeat `id` up to 8 times). The response includes trajectories, RGB-conservation counterexample counts, structural metric ranges and direction changes, and repeated measurement signatures.

Important limitations: observed repeated measurement signatures are NOT complete-state recurrence; correlation is not causality; no native inverse, continuous Jacobian rank, or new theorem is claimed. V6 does not automatically derive mathematically proven laws. Existing V5 runs can be analyzed without modifying the engine.

Tests: `python -m unittest discover -s tests -p 'test_discovery_v6.py'`.
