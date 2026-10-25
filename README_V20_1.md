# V20.1 Native State Verification

Adds `/verification-v201` and `POST /api/v201/verify` (JSON `{ "steps": 1 }`). Pause engine before use. Reports are saved under `research_data/v201/verification/`.

Verification covers observed per-channel RGB totals and simple structural metrics over up to 20 steps. The native `HexState` struct is copied byte-for-byte and restored; V10 serialized fields are also restored. This **does not** restore or prove coverage of C static tracing buffers, Python auxiliary globals, worker timing, or other external state. No inverse of the full engine is provided, and no universal conservation/injectivity claim is made. Run native code and server locally on your device to validate Android integration.
