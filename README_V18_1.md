# V18.1 Native Stage Laboratory

New route: `/stage-lab`. Choose a cell (0 to cell_count-1), select **Arm trace**, then **Step once** or **Run**. Select any of 17 stages to inspect input, four neighbor operands, and output captured by native C. A highlighted cell is shown when it lies among the 128 sampled visualization cells. The engine Run/Pause controls are shared with the terminal; **Freeze display** only pauses this page's rendering.

The stage trace is a bounded one-cell trace and does not expose all arithmetic expressions. The underlying trace buffer reflects the most recent traced engine step; running continuously replaces previous records. The visualization samples only the first 128 cells. For controlled experiments, pause the engine before stepping and disable other background modes as needed.

Termux: `pkg install python clang unzip -y`, unzip, `cd v7work`, `sh start_unified.sh`. Open `http://127.0.0.1:8141/stage-lab`. Native libraries are rebuilt by the included startup process on the target architecture.
