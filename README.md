# CivicConnect

CivicConnect is a citizen service-request system for submitting requests, tracking their progress, and helping staff manage and resolve them. This repository contains the M2 engineering reference pack and the M3 application and verification work.

## Project contents

| Path | What it contains |
|---|---|
| `CivicConnect_Team_PED_Pack.zip` | The preserved M2 engineering pack: lifecycle service, SQLite schema, demo, tests, traceability records, and evidence. |
| `CivicConnect_PED_v2.0.docx` | The M2 project engineering document. |
| `docs/member1_m2/product/` | The M3 server-rendered web application, lifecycle service, schema, styles, and local server. |
| `docs/member1_m2/tests/` | M3 component, black-box, integration, end-to-end, tooling, feature, and web security tests. |
| `docs/member1_m2/evidence/` | M3 test strategy, results, requirement links, and verification notes. |

The ZIP is a preserved M2 reference. The M3 web application is in `docs/member1_m2/`; these are separate project versions and should not be mixed when running commands.

## Run the M3 application locally

Use Python 3.12 and PowerShell. From the repository root, move into the M3 application folder:

```powershell
Set-Location docs/member1_m2
```

For a local demonstration with synthetic accounts, enter a password for those accounts and start the server:

```powershell
$secret = Read-Host 'Choose a local demonstration password' -AsSecureString
$env:CIVICCONNECT_DEMO_PASSWORD = [System.Net.NetworkCredential]::new('', $secret).Password
python product/serve.py --seed-demo
```

Open `http://127.0.0.1:8000`. The demonstration accounts are `citizen-a`, `citizen-b`, `staff-a`, and `staff-b`; use the password entered above. `citizen-a` has a sample request. New citizens can register from the sign-in page. Stop the server with **Ctrl+C**.

The app creates its local database at `data/civicconnect.sqlite3`. The development server binds to this computer only by default. The sample data is synthetic; do not use this local demonstration for real citizen information or public deployment.

To start without demo accounts, run `python product/serve.py` instead. Optional local settings include:

| Variable | Purpose |
|---|---|
| `CIVICCONNECT_DB_PATH` | Choose a different local database file. |
| `CIVICCONNECT_HOST` / `CIVICCONNECT_PORT` | Change the local server address or port. |
| `CIVICCONNECT_SESSION_SECRET` | Set a stable session key of at least 32 bytes. Otherwise a temporary key is generated each time the server starts. |
| `CIVICCONNECT_COOKIE_SECURE` | Set to `true` only when serving over HTTPS. |
| `CIVICCONNECT_ADMIN_SETUP_TOKEN` | Enable first-administrator setup with a private one-time token of at least 32 bytes. Setup closes after an administrator exists. |

Do not commit passwords, tokens, database files, or other secrets.

## Run the M3 checks

From `docs/member1_m2/`, run:

```powershell
python -m compileall -q product tests
python -m unittest discover -s tests -v
python product/performance_smoke.py
```

The regression suite covers the application and its supporting tools. The performance smoke check exercises the documented local lookup scenario; it is not a production capacity test. GitHub Actions also runs the regression checks, Bandit static security analysis, and Gitleaks secret scanning for the M3 workflow.

## What the application supports

- Citizen registration, sign-in, request submission, and access to their own requests.
- Department-scoped staff request queues, search, filters, and lifecycle updates.
- Requester confirmation after resolution, or an explanation to return an unresolved request to In Progress.
- Administrator setup and account, role, and request-category management.
- Management summaries and request lifecycle history.
- Form validation, signed expiring sessions, request-forgery protection, and security response headers.

The app is a local, server-rendered Python application using SQLite. The repository’s M3 release and evidence records control whether requirements are accepted and whether the work is ready for release. A successful local test run alone does not mean the system is production-ready.

## M2 engineering reference pack

To inspect or run the preserved M2 pack, download and extract `CivicConnect_Team_PED_Pack.zip`. Open a terminal in the extracted folder containing `traceability.py`, `product/`, and `tests/`. The pack has its own demo and test instructions in its included `README.md`; do not run its commands from `docs/member1_m2/`.

## More information

- [M3 application instructions](docs/member1_m2/product/README.md)
- [M3 test strategy](docs/member1_m2/evidence/test-strategy.md)
- [M3 requirement matrix](docs/member1_m2/evidence/requirement-matrix.csv)
- [M3 staging notes](docs/member1_m2/evidence/simulated-staging.md)
- [M3 release evidence summary](docs/member1_m2/evidence/release-evidence-summary.md)
- [M2 project engineering document](CivicConnect_PED_v2.0.docx)
- [M2 engineering pack](CivicConnect_Team_PED_Pack.zip)
