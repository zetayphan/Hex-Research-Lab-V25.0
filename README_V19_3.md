# V19.3 Symbolic Collision Analysis

New route: `/collision-v193`. API: `POST /api/v193/analyze`.

This edition adds a fixed-width 24-bit SMT bit-vector model of the six neighbor-dependent stages on a 2×2×2 lattice. With `z3-solver` installed, it searches for distinct complete inputs that produce the same output. SAT results are independently checked against `native_v14.forward`. UNSAT establishes injectivity of the **isolated modeled stage** for the fixed flags, not the complete native engine. UNKNOWN/timeout is inconclusive. The previously established exact GF(2) and disabled-stage identity analyses are retained.

Optional symbolic solver: `python -m pip install z3-solver` (availability on Android/Termux varies). Without it, the program falls back to bounded search and explicitly reports the weaker result.

Results: `research_data/v193/symbolic_audits/`. No native engine state is modified by these investigations.

## Limitations
The isolated Python model must be checked against the current native C source before claiming native equivalence. Full 17-stage composition, auxiliary state, and Android browser integration are not proven.
