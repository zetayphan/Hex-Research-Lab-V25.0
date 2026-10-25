# Hex Unified Research Lab V23.0 — Research Intelligence

Adds /intelligence-v23, GET /api/v23/analysis, POST /api/v23/save.

The analysis reads V22 queue job files and V20.2 saved playback traces. It generates a narrowly defined candidate hypothesis about unchanged selected-cell stage outputs and checks it against separate saved recordings. Contradictory observations are counted; results are explicitly non-proof. Report JSON is saved under research_data/v23/reports.

This release does not modify the C engine, existing experiment queue, saved histories, or terminal/visualization. It does not yet automatically schedule hypothesis-specific new experiments or perform global collision proofs. Job-to-playback linkage is only asserted when identifiers actually match.

Start: cd v7work && sh start_unified.sh ; open http://127.0.0.1:8141/intelligence-v23
