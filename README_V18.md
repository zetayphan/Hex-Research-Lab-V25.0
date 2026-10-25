# V18.0 — Native trace and portable compilation

Start with `sh start_unified.sh`. Both native C libraries are compiled on the current host at startup (Termux ARM64 or Linux).

In `/terminal`, enter `pause`, `trace on 0`, `step 1`, `trace show`. This displays actual values captured *inside* each of the 17 C stage operations for cell 0: input, four neighbor operands, and output. `trace off` disables capture. Tracing is bounded to one selected cell and the most recent native step; it is not a complete trace of every arithmetic subexpression or cell.

The visualization and terminal still use the shared state. Older research routes remain present. No claims are made about full-state reversibility.
