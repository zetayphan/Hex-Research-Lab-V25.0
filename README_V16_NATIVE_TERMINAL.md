# V16 — Native Hex Terminal arithmetic engine

This builds on V15. A separate C11 shared library (`src/terminal_native.c`) evaluates 24-bit hexadecimal operations: add, subtract, multiply, XOR, AND, OR, rotate-left, rotate-right, integer divide and modulo. Inputs and outputs are masked to 24 bits. Division by zero is rejected. The library is compiled automatically by `src/server.py` using `cc` (Termux: `pkg install clang`).

Open `/terminal` and use the Native C hexadecimal calculator. The Run, Pause, and Step controls still act on the shared Hex Studio engine, and the live visualization remains available at `/visualization`.

**Scope:** Native calculator computations are performed in C, but do not modify the live simulation cells. The separate state-trace window continues to show sampled cell deltas and stage checksums, not a complete instruction-level trace. The existing 17-stage engine remains unchanged.
