# V23.2 — Automatic evidence linking and revalidation

V22 queued runs now link their generated V20.2 native playback JSON files to the queue job and experiment ID, using verified identifiers and atomic file replacement. The V23.1 cycle review reads these linked records directly and evaluates the selected-cell stage input/output equality hypothesis. The browser refreshes the cycle list every five seconds. Use the Review button to refresh a particular cycle's result.

**Scope:** This is observational stage equality only, not a proof of reversibility or conservation. Jobs completed before this release may lack explicit links and are correctly reported as insufficient evidence. No existing historical recordings are deleted. Queue execution still requires the Termux server to remain active.
