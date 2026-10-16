# CivicConnect application

This application implements a server-rendered citizen request workflow using Python's standard library and SQLite. It runs as one local process; it does not introduce a separate frontend framework or an internal REST interface.

## Start locally

Run these commands from `docs/member1_m2` in PowerShell with Python 3.12:

```powershell
$secret = Read-Host 'Local demonstration password' -AsSecureString
$env:CIVICCONNECT_DEMO_PASSWORD = [System.Net.NetworkCredential]::new('', $secret).Password
python product/serve.py --seed-demo
```

Open `http://127.0.0.1:8000`. Synthetic demonstration accounts are `citizen-a`, `citizen-b`, `staff-a`, and `staff-b`; the password is the one entered above. `citizen-a` has a sample request. New citizens can register from the sign-in page.

The local database is created at `data/civicconnect.sqlite3`, which is ignored by Git. The default server binds to loopback. Set `CIVICCONNECT_DB_PATH` to use another local database path, `CIVICCONNECT_HOST` and `CIVICCONNECT_PORT` to change the listener, or `CIVICCONNECT_SESSION_SECRET` to supply a stable local session key. Without that variable, a random process-only key is generated and sessions end when the server stops. Set `CIVICCONNECT_COOKIE_SECURE=true` only when serving over HTTPS.

To bootstrap the first administrator on a database without an administrator, configure a private one-time setup token of at least 32 characters before starting the server, open `/setup/administrator`, and enter the token in the form. For example, generate a local token with `[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))` and set it as `CIVICCONNECT_ADMIN_SETUP_TOKEN`. Do not commit or share the token. Setup is disabled once an administrator exists; account creation and role changes then require administrator sign-in.

Stop the server with Ctrl+C. Demo data is synthetic; do not use demonstration accounts or the local development server for real citizen information or public deployment.

## Implemented workflow

- Citizen registration and sign-in with salted PBKDF2 password hashes.
- Server-side validation of title (5–120 characters), description (10–2,000), location (3–200), and active category.
- Server-generated request references and persistence of requester, submission time, department, and category label.
- Citizen-owned request lists and details; department-scoped staff lists and details.
- Staff request search by reference/title, category/status/assignee filters, and controlled sorting, with the department boundary applied inside the database query.
- Staff lifecycle transitions with the existing policy, optimistic version check, and atomic status/history persistence. When staff mark a request resolved, its citizen can confirm closure or explain why it remains unresolved and return it to In Progress; no response leaves it Resolved for later follow-up.
- First-administrator bootstrap that closes after an administrator exists; administrator account/role/deactivation and controlled-category maintenance.
- Management summaries with date/category/status filters, open/overdue and lifecycle counts, category/status breakdowns, assignee and request age.
- Signed, expiring HTTP-only session cookies, request-forgery tokens on forms, escaped user content, and current account-status checks on requests.
- Login throttling by account and remote address, generic invalid-credential feedback, security response headers, and a token-protected one-time administrator bootstrap.

The initial category list contains Water and Roads, mapped to their corresponding staff departments. An administrator can retire a category without removing the historical label stored on past requests. Outbound email/SMS is deferred; request history displays status, event time and explanation. The [M3 verification strategy](../evidence/test-strategy.md), [local demonstration instructions](../evidence/simulated-staging.md), and [release evidence summary](../evidence/release-evidence-summary.md) describe the tested behavior and evidence. All four team members confirmed that the planned M3 requirements, tests, checks and supporting evidence were tested, checked and verified, and completed the required approvals for the local SEN381 school-project release on 16 October 2026. See the [team verification record](../evidence/team-release-verification.md).

## Code layout

| File | Responsibility |
|---|---|
| `lifecycle.py` | Account authentication, request validation/submission/query, transition policy, and SQLite transactions. |
| `schema.sql` | Accounts, credentials, categories, requests, lifecycle events, constraints, and lookup indexes. |
| `web.py` | Standard-library WSGI forms, sessions, authorization boundaries, and HTML rendering. |
| `static/styles.css` | Responsive visual system, accessible interaction states, and reduced-motion-aware animations. |
| `serve.py` | Local configuration, optional synthetic seed data, and the development HTTP server. |
| `demo.py` | Offline service demonstration of a committed lifecycle change and requester history read. |
| `../tests/` | Component, black-box, integration, end-to-end and security regression checks. |
| `../evidence/` | Requirement links, simulated staging procedure and release readiness evidence. |

`SqliteLifecycleStore.initialise()` creates the current schema and adds missing request-detail columns to an earlier database. The migration preserves earlier request rows and fills new fields with legacy defaults. State and lifecycle events remain committed in a single transaction. `history()` allows a citizen to read their own request and staff to read requests in their department.
