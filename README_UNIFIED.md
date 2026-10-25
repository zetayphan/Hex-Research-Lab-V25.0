# Hex Unified Research Lab V1

Combines the original Hex Studio Pro X V10.5 dashboard/native C engine, Hex Terminal Pro X V5 command shell, and the four-page unified theorem PDF without replacing the existing Canvas/WebGL rendering.

## Termux quick start
```sh
pkg update && pkg install python clang unzip -y
termux-setup-storage
cd ~/storage/downloads
unzip Hex_Unified_Research_Lab_V1.zip -d ~/hex_unified
cd ~/hex_unified
sh start_unified.sh
```
Open http://127.0.0.1:8141/ in your browser. In another Termux session:
```sh
cd ~/hex_unified
sh terminal.sh
```
The terminal and dashboard connect to the **same** local engine on port 8141. In a third session, use `python3 theorem_lab.py --example-only` for a pure theorem example or `python3 theorem_lab.py --steps 1` to observe one live engine step. WARNING: the latter advances the live simulation. If port 8141 is occupied, stop the old process or use `HEX_STUDIO_PORT=8155 sh start_unified.sh` and the same environment variable for terminal/theorem lab.

## Research scope
- `THEOREM.pdf` contains the mathematical assumptions and proofs.
- `theorem_lab.py` checks the constructive three-cycle example and measures before/after RGB channel totals from actual engine states.
- The Studio engine has both conservative and intentionally transformative/nonconservative stages; conservation is **not** assumed for a full tick.
- No general inverse of the full native engine has been established, and the empirical check does not claim one.
- Structural-coordinate Jacobian rank and continuum fluid PDEs are not implemented by the native finite-state engine; these remain mathematical models, not measured physical dimensions.
- The existing browser live interaction runs while its tab is open; this package does not promise browser-independent live automation.
- Existing Studio and Terminal tests are retained, and an additional theorem example test is included.
