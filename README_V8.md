# Hex Unified Research Lab V8 — Mathematical Research Intelligence

Preserves the V7 engine, dashboards, and tests, adding `/research-v8` and `/api/v8/report?id=RUN1&id=RUN2`.

Select one discovery run and one or more validation runs. V8 evaluates the existing V7 hypotheses, calculates observed validation accuracy and descriptive Wilson intervals, records SHA-256 hashes of the source JSONL files, suggests follow-up experiments, and exports a Markdown report (`&format=md`).

V8 does **not** automatically design or execute new experiments. It does not prove hypotheses, guarantee statistical independence, or establish native reversibility or new physical dimensions.

Start with `sh start_unified.sh`, then open `http://127.0.0.1:8141/research-v8`. Create historical runs first at `/experiments-v5`.

Tests: `python -m unittest discover -s tests -p 'test_research_v8.py'`.
