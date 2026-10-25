# Hex Unified Research Lab V20.0

Adds simultaneous bounded tracing of up to 16 cells within a **single** native 17-stage `hex_step` call, retaining all V19.3 research functionality. The engine itself still runs the same mathematical transformation; the new native trace API records operands and expressions for selected cells without replaying the step. Trace output excludes optional post-processing after the 17 stages.

Start using `sh start_unified.sh` in `v7work`, open `/trace-v20`, pause the engine, arm selected cells, then step once. Native API: `hex_multi_config`, `hex_multi_count`, `hex_multi_get`, `hex_multi_expression`. HTTP: POST `/api/v20/trace` with `{"cells":[0,1,2]}`, GET `/api/v20/trace`. Use the terminal `step 1` command to execute one tick.

**Limits:** maximum 16 unique cell indices; trace data is in-memory and replaced on every engine step. Not a proof of global reversibility. The native trace configuration is process-global and intended for one engine instance guarded by the server lock. Prior single-cell tracing remains available, but reconfiguring it can override simultaneous tracing; re-arm V20 tracing if necessary.
