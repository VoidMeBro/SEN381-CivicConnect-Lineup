# CivicConnect application

This application implements a server-rendered citizen request workflow using Python's standard library and SQLite. It runs as one local process; it does not introduce a separate frontend framework or an internal REST interface.

## Start locally

Run these commands from `docs/member1_m2` in PowerShell:

```powershell
$secret = Read-Host 'Local demonstration password' -AsSecureString
$env:CIVICCONNECT_DEMO_PASSWORD = [System.Net.NetworkCredential]::new('', $secret).Password
python product/serve.py --seed-demo
```

Open `http://127.0.0.1:8000`. Synthetic demonstration accounts are `citizen-a`, `citizen-b`, `staff-a`, and `staff-b`; the password is the one entered above. `citizen-a` has a sample request. New citizens can register from the sign-in page.

The local database is created at `data/civicconnect.sqlite3`, which is ignored by Git. The default server binds to loopback. Set `CIVICCONNECT_DB_PATH` to use another local database path, `CIVICCONNECT_HOST` and `CIVICCONNECT_PORT` to change the listener, or `CIVICCONNECT_SESSION_SECRET` to supply a stable local session key. Without that variable, a random process-only key is generated and sessions end when the server stops. Set `CIVICCONNECT_COOKIE_SECURE=true` only when serving over HTTPS.

Stop the server with Ctrl+C. Demo data is synthetic; do not use demonstration accounts or the local development server for real citizen information or public deployment.

## Implemented workflow

- Citizen registration and sign-in with salted PBKDF2 password hashes.
- Server-side validation of title (5–120 characters), description (10–2,000), location (3–200), and active category.
- Server-generated request references and persistence of requester, submission time, department, and category label.
- Citizen-owned request lists and details; department-scoped staff lists and details.
- Staff lifecycle transitions with the existing policy, optimistic version check, and atomic status/history persistence.
- Signed, expiring HTTP-only session cookies, request-forgery tokens on forms, escaped user content, and current account-status checks on requests.

The initial category list contains Water and Roads, mapped to their corresponding staff departments. Category/account administration and management reporting remain outside this application slice. Usability, performance, availability, deployment, and production-scale acceptance require separate evidence.

## Code layout

| File | Responsibility |
|---|---|
| `lifecycle.py` | Account authentication, request validation/submission/query, transition policy, and SQLite transactions. |
| `schema.sql` | Accounts, credentials, categories, requests, lifecycle events, constraints, and lookup indexes. |
| `web.py` | Standard-library WSGI forms, sessions, authorization boundaries, and HTML rendering. |
| `serve.py` | Local configuration, optional synthetic seed data, and the development HTTP server. |
| `demo.py` | Offline service demonstration of a committed lifecycle change and requester history read. |

`SqliteLifecycleStore.initialise()` creates the current schema and adds missing request-detail columns to an earlier database. The migration preserves earlier request rows and fills new fields with legacy defaults. State and lifecycle events remain committed in a single transaction. `history()` allows a citizen to read their own request and staff to read requests in their department.
