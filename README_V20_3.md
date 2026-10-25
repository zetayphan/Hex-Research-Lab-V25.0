# V20.3 Automated Research Reports

Based on the working V20.2 Playback Fixed release. Navigate to `/reports-v203`, choose a saved V20.2 playback run, optionally choose a second run, and generate a Markdown report. The report is saved in `research_data/v203/reports/` and can be downloaded in the browser. The report contains native stage input/output, 24-bit modular deltas, XOR differences, arithmetic expressions, comparison tables, and SHA-256 hashes of the saved evidence files.

This feature reads recorded selected-cell traces only. It cannot infer global RGB conservation, complete-state reversibility, or whole-lattice evolution from those traces. For these properties, consult separate native-state verification experiments. It does not modify the running engine.

Termux: `cd ~/hex_unified_v20_3/v7work && sh start_unified.sh`. URL: `http://127.0.0.1:8141/reports-v203`.
