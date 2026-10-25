# Hex Unified Research Lab V2

V2 preserves the V1 engine, Studio dashboard, terminal, and theorem. New research dashboard: **http://127.0.0.1:8141/research**.

## Termux
```sh
pkg update && pkg install python clang unzip -y
termux-setup-storage
cd ~/storage/downloads
unzip Hex_Unified_Research_Lab_V2.zip -d ~/hex_unified_v2
cd ~/hex_unified_v2
sh start_unified.sh
```

Open `/research` for real-time read-only sampling (1 second intervals); click **Step engine once** to advance manually. The main Studio remains at `/`. In another Termux session, `cd ~/hex_unified_v2 && sh terminal.sh`. To change ports, set `HEX_STUDIO_PORT=8155` when starting.

## Research limitations
- The RGB conservation card shows actual differences, including failures of conservation; it does not claim full-engine conservation.
- Unique hex values and adjacent-cell transitions are discrete structural proxies, **not** new physical dimensions or differential rank.
- The cyclic permutation is a mathematically exact demonstration separate from the actual engine.
- No complete inverse of the engine, continuum fluid solver, or proof of coupling is claimed.
- Sampling runs while the browser is open. The original engine's own run state is unchanged.
