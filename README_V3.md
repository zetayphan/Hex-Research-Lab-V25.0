# Hex Unified Research Lab V3 — Mathematical Verification Engine

Preserves V2 Studio (`/`), research dashboard (`/research`), terminal, and PDF. Adds **`/verification`** with auto-refreshing exact reference permutation, differentiable structural-rank surrogate, and native observational metrics. The verification page does **not** step the engine by itself.

## Termux
```sh
pkg update && pkg install python clang unzip -y
termux-setup-storage
cd ~/storage/downloads
unzip Hex_Unified_Research_Lab_V3.zip -d ~/hex_unified_v3
cd ~/hex_unified_v3
sh start_unified.sh
```
Open `http://127.0.0.1:8141/verification`. If port 8141 is occupied, run `HEX_STUDIO_PORT=8155 sh start_unified.sh` and open port 8155 instead.

## Command-line verification
```sh
python verify_v3.py                 # exact models only; no server needed
python verify_v3.py --live          # observe running server without stepping
python verify_v3.py --live --steps 1 # advance server once and compare
python -m unittest discover -s tests -p 'test_verification_v3.py'
```

**Scope:** The three-coordinate cyclic permutation is mathematically invertible and conservative; this does NOT prove native engine reversibility. Jacobian rank is computed for a smooth surrogate, not discrete native states. Native RGB deltas and structural proxies are observations, not guaranteed invariants. Background recording, a complete native inverse, and a coupled fluid PDE are not implemented in V3.
