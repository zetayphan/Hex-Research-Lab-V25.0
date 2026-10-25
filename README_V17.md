# V17 — Native engine terminal

The terminal at `/terminal` now issues commands to the **same native C `src/engine.c` state** used by the live visualization. It does not replace the 17-stage engine with the separate calculator. The calculator remains available as a utility.

Commands: `help`, `status`, `run`, `pause`, `step [count]`, `read <index>`, `set <index> <hex24>`, `cells [start] [count]`, `stages`.

`step` calls the existing complete simulation step, including the 17 native stages and the configured post-processing. `set` modifies a cell through `hex_set_cell` in the original C engine. `stages` reports native stage checksums and changed-cell counts, **not** an instruction-by-instruction trace. The visualization shares the same state and responds to changes. Pause before manual mutation. These operations can affect concurrent experiments; avoid using the command terminal during controlled runs.

Run: `cd v7work && sh start_unified.sh`; open `http://127.0.0.1:8141/terminal`.
