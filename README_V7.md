# Hex Unified Research Lab V7 — Mathematical Hypothesis Engine

V7 preserves V6 and adds candidate hypothesis generation from a discovery run and checks those hypotheses against other historical V5 runs.

Launch: `sh start_unified.sh`, then open `http://127.0.0.1:8141/hypotheses-v7`.

Create at least two runs at `/experiments-v5`; choose the first as discovery and one or more different runs as held-out validation. API: `/api/v7/hypotheses?id=DISCOVERY_ID&id=VALIDATION_ID` (up to eight runs total).

Candidate hypotheses include observed RGB conservation, constant structural measurements, and monotonic structural trends. Results explicitly show counterexamples and sample counts. They do not prove universal laws, native reversibility, or dimensional growth. Run independence is a research-design responsibility.

Test: `PYTHONPATH=.:src python -m unittest discover -s tests -p test_hypothesis_v7.py`.
