# Hex Unified Research Lab V9 — Experimental Design & Replication

V9 preserves the V8 research system and adds `/design-v9` with pre-registered experiment plans, SHA-256 plan fingerprints, downloadable JSON plans, and descriptive comparisons of multiple saved V5 historical runs.

The plan recommends matched step counts, recording initial conditions, and held-out validation. It does **not** automatically reset or seed the native engine, nor does it establish that sequential runs have matched initial states. Comparison metrics are descriptive and are not calibrated statistical tests.

## Run in Termux

From this directory: `sh start_unified.sh` then open `http://127.0.0.1:8141/design-v9`.

Create experiments at `/experiments-v5`, refresh V9's run selector, select multiple runs, and compare. Use **Generate plan** and **Download plan JSON** before collecting runs to document intended parameters.

## Tests

`python -m unittest discover -s tests -p 'test_design_v9.py'`
