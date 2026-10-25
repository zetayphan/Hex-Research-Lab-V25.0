# V12 — Reversibility Investigation

Open `/reversibility-v12` after starting `sh start_unified.sh`.

This version adds a mathematically invertible cyclic-permutation **reference** map, verifies its forward/inverse round trip, and compares two native-engine trajectories after restoration of the existing serialized state. The UI reports matching frame counts and exports a JSON investigation.

**Limits:** The 17-stage native pipeline has no implemented inverse in this release. Existing serialization may omit future-relevant engine state; restoration and repeatability are not proofs of complete-state invertibility. V12 deliberately reports `native_inverse_verified: false` and `complete_state_verified: false`.

Run tests: `python -m unittest discover -s tests -p 'test_reversibility_v12.py'`.
