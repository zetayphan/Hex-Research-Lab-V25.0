# Hex Unified Research Lab V14 — Neighbor-Dependent Stage Investigation

Start with `sh start_unified.sh` from this directory. Open `/native-v14` on the server (default port 8141).

V14 implements the six neighbor-dependent C stage formulas in Python and checks conditional recovery when the **original neighbor frame** is provided as side information. It does **not** prove these stages are globally injective, nor provide an inverse using only their output. The source SHA-256 is displayed to support source review. Existing V13 and earlier tools are preserved.

Run `python -m unittest discover -s tests -p 'test_native_v14.py'`.

Caution: this is a mathematical investigation, not proof of complete native engine reversibility; side information can contain as much information as the original input.
