# V24.4 Evidence-guided hypothesis selection

Adds `GET /api/v244/recommend` and a **Recommend hypothesis** button on `/cycle-v231`.
Uses V24 discovery/validation classifications to rank the four V24.3 predicates for further investigation. The recommendation is deterministic, bounded, and transparent. It never automatically queues a job: the user reviews and submits through the existing V22 queue.

The priority score is a workflow heuristic, not a statistical confidence measure. No evidence returns `NO_EVIDENCE` and requires a saved playback trace. All existing native engine, queue, and evidence-linking logic is unchanged.
