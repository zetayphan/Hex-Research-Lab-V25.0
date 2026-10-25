# V11 — Recorded-state mathematical audit

New page: `/audit-v11`. It measures RGB conservation across native steps, detects recurrence of serialized frames, and verifies that the initial serialized frame can be restored. Results can be downloaded as JSON.

## Critical scope
The native pipeline includes transformative operations, so RGB conservation is not assumed. No inverse of the full native pipeline is provided or claimed. V11 does **not** capture or prove that all future-relevant native or auxiliary state is serialized; therefore complete-state recurrence and invertibility remain open questions. Recurrence requires identical recorded frames, including tick, which may prevent detection of cell-only cycles.

## Use
Pause the simulation; disable bonding and persistent network features; stop the autonomous recorder and any V5 experiment. Start `sh start_unified.sh`, then open `http://127.0.0.1:8141/audit-v11`. Choose 1–500 steps and run the audit. The starting serialized frame is restored afterward.

## Test
`python -m unittest discover -s tests -p 'test_audit_v11.py'`
