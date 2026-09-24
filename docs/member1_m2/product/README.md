# CivicConnect initial lifecycle application slice

Run from the parent Member 1 pack directory: `python product/demo.py`.
Tests: `python -m unittest discover -s tests -v`.

Python 3.11+ and its standard sqlite3 module are sufficient. Verified runtime versions are in evidence/verification.txt. There are no packages to install, secrets, environment variables, external services or network calls. The demo creates and removes its own temporary synthetic database.

`schema.sql` creates accounts, requests and lifecycle_events, their constraints and history index. `SqliteLifecycleStore.initialise()` applies this idempotent initial schema; no schema upgrade is provided because this is its first revision. `lifecycle.py` contains the coordinator, independent policy and transaction store. `demo.py` is the runnable interface. `tests/test_lifecycle.py` exercises success, denial, rollback and conflict paths.

The transition contract returns reference/status/version/explanation after commit. Forbidden covers absent or inaccessible requests; InvalidTransition covers invalid state/fields; Conflict requires reloading and revalidating. sqlite3 persistence exceptions propagate after rollback. No failed command reports success. History returns only the active owning citizen's current status and ordered committed events.

This is a single-process logical architecture with a file-backed SQLite store. The service accepts an authenticated actor ID from its caller; it does not authenticate passwords. Full web UI, networking, deployment and load acceptance are outside this initial slice. Do not expose the CLI actor parameter as an unauthenticated web API.
