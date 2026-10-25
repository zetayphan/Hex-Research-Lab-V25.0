# Hex Unified Research Lab V19.2 — Algebraic Reversibility & Collision Analysis

New page: `/collision-v192` and JSON API: `POST /api/v192/analyze`.

- Stage 8 (index 7): exact GF(2) linear-algebra rank/nullspace classification for the entire 2×2×2, 24-bit-per-cell model. A nonzero nullspace vector yields a directly reverified collision witness; full rank proves injectivity for this isolated stage.
- Stage 4 (index 3) with extension flag **off**: exact identity proof, hence bijective for this isolated stage.
- Other coupled stages: preserved V19.1 bounded enumeration and seeded randomized search. No collision found is **unresolved**, never proof of injectivity.
- All reported witnesses are independently recomputed with the source-aligned stage model and saved to `research_data/v192/algebraic_audits/`.

These results do **not** prove full 17-stage native engine reversibility. No new dependency is required. Start with `sh start_unified.sh` from `v7work`, then open `/collision-v192`.
