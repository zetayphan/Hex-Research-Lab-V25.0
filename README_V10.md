# V10 Controlled State Evolution

V10 adds /controlled-v10 and POST /api/v10/trial. Pause the engine and stop the V4 recorder and V5 experiments before running. Disable all network/bonding modes. Each replica restores the same serialized native state and executes an identical number of steps. SHA-256 fingerprints of each serialized frame are compared. The initial frame is restored at the end, even if a trial fails.

Limits: 2–12 replicates, 1–200 steps. This is a repeatability test, not a proof of reversibility or full native-state equivalence. It is restricted to disabled bond/network modes because legacy restore intentionally drops some network state. The native engine may have unexposed auxiliary state; matching fingerprints cannot rule this out. Full Android browser testing is pending.

Run: `sh start_unified.sh`, then open `http://127.0.0.1:8141/controlled-v10`.
Test: `python -m unittest discover -s tests -p test_controlled_v10.py`.
