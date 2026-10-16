# Simulated Staging Environment

## Environment

The assessor-accessible staging equivalent is an isolated local run of the exact repository checkout under review. It uses the same Python standard-library application and SQLite schema/migrations as the submitted source, but an isolated database with synthetic records. It does not use production or real citizen data and does not claim public internet availability.

## Start procedure

From `docs/member1_m2` in PowerShell:

```powershell
$env:CIVICCONNECT_DB_PATH = "$PWD/.test-tmp/staging.sqlite3"
$env:CIVICCONNECT_HOST = "127.0.0.1"
$env:CIVICCONNECT_PORT = "8000"
$env:CIVICCONNECT_ADMIN_SETUP_TOKEN = [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
python product/serve.py
```

Open `http://127.0.0.1:8000/setup/administrator`, create the isolated administrator, and add synthetic Management, Staff and Citizen accounts. Use a citizen account to submit a request, a staff account in the matching department to accept and resolve it, then verify the history as the requester and the summary as Management. Stop the server with Ctrl+C and remove the isolated database after the demonstration.

The first-administrator token must remain private and must not be committed or copied into presentation materials. The application refuses administrator setup without the token and refuses setup after an administrator exists.

## Limitations

This is a repeatable local staging simulation, not a managed deployment. It does not verify TLS termination, public network behavior, production database operations, backup/restore, rollback in a hosted environment, continuous availability, monitoring or the NFR-04 business-hour availability target. CI uses an isolated temporary database and synthetic data; the demonstration should use the same identified commit as the release candidate.
