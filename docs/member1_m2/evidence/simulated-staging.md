# Local M3 Demonstration Environment

## Scope

The approved M3 release is intended to run locally for the SEN381 school project. It uses the integrated Python web application and SQLite database in this folder. Use synthetic demo data; do not put real citizen information into the demonstration database.

This file gives local setup instructions. The recorded 13-check staging result in the repository root is a separate lifecycle-service experiment and is not a test report for this web application.

## Start the local application

From `docs/member1_m2` in PowerShell:

```powershell
$secret = Read-Host 'Choose a local demonstration password' -AsSecureString
$env:CIVICCONNECT_DEMO_PASSWORD = [System.Net.NetworkCredential]::new('', $secret).Password
New-Item -ItemType Directory -Force .test-tmp | Out-Null
$env:CIVICCONNECT_DB_PATH = "$PWD/.test-tmp/demo.sqlite3"
python product/serve.py --seed-demo
```

Open `http://127.0.0.1:8000`. The synthetic accounts are `citizen-a`, `citizen-b`, `staff-a` and `staff-b`, all using the password entered above. `citizen-a` has a sample request. New citizens can register from the sign-in page. Stop the application with **Ctrl+C**.

The app binds to `127.0.0.1` by default and keeps its database in the local project folder specified above. The demonstration password is held only in the current PowerShell session; do not commit it.

## Demonstration path

Use a citizen account to submit a request and view its status. Sign in as staff to find and process a request in the matching department. Sign in as management to view the summary report. The automated regression suite covers these user paths and role boundaries; see `test-strategy.md` and `member2-test-results.txt`.

This local setup is the release demonstration environment for the school project. All four team members confirmed the planned M3 requirements and checks as verified and completed the required approvals on 16 October 2026; see `team-release-verification.md`. A hosted server or public URL is not required by the approved scope.
