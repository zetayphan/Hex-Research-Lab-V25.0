# Hex Unified Research Lab V13 — Native Stage Audit

Open `/native-v13` after starting `sh start_unified.sh`.

This release audits the actual `src/engine.c` 17-stage `hex_step` switch, rather than only a reference rotation. It establishes isolated-stage inverses for 11 stages (7 identities, 4 pointwise modular/XOR/rotation transforms). The six neighbor-dependent simultaneous-update stages are explicitly **unresolved**, not assumed reversible or irreversible. A full-state inverse for `hex_step`, including stage metadata, tick, checksum, flags, and other auxiliary state, is **not** established.

The API `/api/v13/stages` includes a source SHA-256 fingerprint. Inverse routines apply to isolated arrays only, not live engine rewinding. Re-review classifications after modifying the C source.

Run targeted tests: `python -m unittest discover -s tests -p 'test_native_stage_v13.py'`.
