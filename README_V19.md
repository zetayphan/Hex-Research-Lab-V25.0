# Hex Unified Research Lab V19 — Controlled Native Trace Experiments

V19 adds `/lab-v19`, an experiment interface with replay-based multi-cell tracing, serialized-frame snapshots, and RGB conservation auditing. All V18.2 Clean routes and native engine source remain available.

## Termux

```sh
pkg install python clang unzip -y
unzip Hex_Unified_Research_Lab_V19.zip -d ~/hex_unified_v19
cd ~/hex_unified_v19/v7work
sh start_unified.sh
```

Open http://127.0.0.1:8141/lab-v19 . Pause the engine using the terminal before running V19 experiments. Saved experiment reports live in `research_data/v19` and snapshot JSON files in `research_data/v19/snapshots`.

## Scope and limitations

The native C tracing interface captures **one cell per step**, so V19 restores the same serialized starting frame and replays the engine once per selected cell. It does not capture multiple cells simultaneously in a single native execution. The `replicated_recorded_state` flag compares serialized native fields across those replays; it does not establish hidden-state equivalence. RGB conservation results are observations, not assumed invariants. Snapshot restore covers the existing V10 serialized state representation, not all possible future-relevant internal state.

## Verification

Local native build and HTTP smoke test: GET `/lab-v19` 200, POST terminal `pause` succeeded, POST `/api/v19/experiment` with cells `[0,1]` returned 17 native stage records for each replay. Android/Termux browser testing remains outstanding.
