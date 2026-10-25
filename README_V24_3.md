# V24.3 — Multi-Hypothesis Targeted Research

Based on V24.2, retaining the fixed V22 queue and native engine.

Open `/cycle-v231`. Choose one of four stage-level predicates:
- `unchanged_cell`: output equals input
- `zero_output`: output equals zero
- `low_byte_preserved`: low 8 bits match
- `parity_preserved`: least-significant bits match

Save at least one native trace via `/playback-v202` before proposing a targeted run. Discovery evidence need not support the candidate: contradicted hypotheses are still testable. Queued experiments run through V22; V23.2 linkage is used to review recorded evidence. The selected predicate is stored in each cycle plan and applied to linked playback records. No result proves a global invariant.

Install in Termux by extracting the ZIP to `~/hex_unified_v24_3`, then run `cd ~/hex_unified_v24_3/v7work && sh start_unified.sh`. Open `http://127.0.0.1:8141/cycle-v231`.

Tests: `python -m unittest discover -s tests -p 'test_v243_hypotheses.py'`.
