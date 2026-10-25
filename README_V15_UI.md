# Hex Unified Research Lab — navigation and terminal interface

Run `sh start_unified.sh` and open http://127.0.0.1:8141/ .

- `/` and `/home`: new homepage with Back and Home navigation.
- `/terminal`: direct native-state hexadecimal comparison terminal, native stage checksums, Run/Pause and Step.
- `/visualization`: live RGB lattice projection, Run/Pause and Step.
- `/legacy`: original Hex Studio dashboard.
- All historical research dashboard routes remain unchanged.

**Shared controls:** Run/Pause in either new window controls the SAME native engine. The terminal displays native hexadecimal state values, per-sample modular differences and XOR, and stage checksums; it does not expose every internal arithmetic instruction. Visualization is a projected native RGB lattice sample rather than the original WebGL renderer (still at `/legacy`). Both poll while open; server evolution continues without browser if Run is enabled.
