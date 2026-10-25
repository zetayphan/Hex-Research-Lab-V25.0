# Hex Unified Research Lab V18.2 — Native arithmetic trace & history

V18.2 extends V18.1. Start with `sh start_unified.sh` inside `v7work` (Termux: `pkg install python clang`). Native libraries are rebuilt locally for your CPU. Open `/stage-lab` or `/terminal`.

## Terminal workflow

```
pause
trace on 0
step 1
trace detail
trace save
```

The C engine records one selected cell across 17 stages. `trace detail` displays the C-computed operation expression, input, operand and output. `trace save` writes a JSON record under `research_data/native_traces_v182/`. The Stage Lab has a Save trace button; `/api/v182/history` lists saved record identifiers. Files survive restarts if the project directory is preserved.

## Scope and limitations

- Tracing captures selected-cell stage computations **during native C execution**, not inferred state differences.
- Identity stages are labeled `identity`; arithmetic descriptions summarize the corresponding native expression, not every CPU instruction.
- Other cells, optional RGB/network post-processing, and external state are **not** fully traced. The save operation records the last captured trace, not an automatically continuous trace history.
- This does not establish conservation or reversibility of the complete engine.
- Full Android browser end-to-end validation is outstanding.
