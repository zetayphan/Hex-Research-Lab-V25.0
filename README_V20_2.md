# Hex Unified Research Lab V20.2 — Native Stage Playback

V20.2 adds saved simultaneous-trace playback and per-stage comparison. It does not reconstruct a complete stage-by-stage lattice or modify the live native state during playback.

Open `/playback-v202`. Pause the engine, configure 1–16 cells at `/trace-v20`, execute one step, and capture the resulting trace in V20.2. Saved traces live under `research_data/v202/playback/`.

Captured traces are from the most recent native step; do not step again between tracing and capture.
