# Hex Unified Research Lab V19.1 — Global Reversibility & Collision Analysis

This edition preserves the V19 terminal-first interface, native engine, visualization, experiments and previous research tools. It adds `/collision-v191` to investigate all six coupled neighbor-dependent stages.

## Method and limits

The Python model in `native_v14.py` is aligned to the six formulas in `src/engine.c`. For a fixed 2×2×2 lattice, fixed flags and 24-bit arithmetic, the investigator exhaustively enumerates a **restricted input alphabet** (up to four values per cell) and optionally samples additional seeded random 24-bit inputs. The search stops when two distinct inputs yield identical output vectors.

A saved witness (`input_a`, `input_b`, `shared_output`) is a constructive proof of non-injectivity of the **isolated tested stage on that lattice**, assuming the source-aligned model accurately represents the native stage. Failure to find a collision is *not* a proof of injectivity, even if the restricted alphabet was exhausted. No claim is made about the entire engine or hidden state.

The tool does not modify the live simulation. Each report includes a SHA-256 fingerprint of `src/engine.c`, configuration, random seed, test count, classification and optional collision witness.

## Run in Termux

Install `python clang unzip` and extract the ZIP to `~/hex_unified_v19_1`. Then:

```sh
cd ~/hex_unified_v19_1/v7work
sh start_unified.sh
```

Open `http://127.0.0.1:8141/collision-v191` or use the homepage link. Results are saved under `research_data/v191/collision_audits/`.

## Tests

```sh
python -m unittest discover -s tests -p 'test_collision_v191.py' -v
```

The engine libraries are compiled on the target device by the existing startup process.
