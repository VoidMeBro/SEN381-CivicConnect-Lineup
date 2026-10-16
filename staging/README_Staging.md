# CivicConnect staging environment (simulated) - runbook

## What this is
A scripted, isolated, single-host staging environment for the release candidate. It is a credible simulation, not a real server: no hosting account, TLS, process supervisor or monitoring exists in it. The gap is recorded as R-09, R-22 and TD-011.

## Layout created by deploy_staging.py
```
<env-root>/
  releases/<rc-id>/        copy of the release files + release.json (hashes, versions, time)
  current -> releases/...  symlink the verification and load scripts use
  data/                    staging database (synthetic accounts and requests only)
  backups/                 SQLite online backups
  logs/
```
The rc-id is `RC-M3-candidate-` plus the first 12 characters of a SHA-256 fingerprint over the release files listed in staging.config.json. Change a file and the id changes.

## Controlled configuration
Everything configurable is in staging/staging.config.json: environment name, release file list, paths, controls (synthetic data only, zero secrets, no network, timezone Africa/Johannesburg, 5-second SQLite busy timeout) and the NFR-03 load profile. The scripts refuse to run unless `CIVICCONNECT_ENV=staging` is set, so they cannot be pointed at a real database by accident. No credentials or environment secrets are needed.

## Run
Python 3.11 or later, no packages.
```bash
export CIVICCONNECT_ENV=staging
python staging/deploy_staging.py   --env-root /tmp/cc-staging
python staging/verify_staging.py   --env-root /tmp/cc-staging --out evidence/staging_verification.json
python staging/load_test.py        --env-root /tmp/cc-staging --out evidence/perf_nfr03_profile.json
```
PowerShell: `$env:CIVICCONNECT_ENV="staging"`. On Windows creating the `current` symlink needs Developer Mode or an elevated shell.

## Critical journey verified (ST-03)
FR-13 with FR-05 and FR-08: staff accept a Submitted request with assignee and due time, move it to In Progress, Resolved and Closed; after each commit the owning citizen reads status, explanation and ordered history from a separate connection. ST-05 to ST-12 cover unauthorised, invalid and stale attempts. The registration, submission and staff-queue journeys cannot be verified because those functions are not in the release candidate.

## Performance test
`load_test.py` measures SqliteLifecycleStore.history(actor, reference), the requester status lookup. Justification: NFR-03 is the only requirement with a numeric load target and this is the only lookup the release candidate implements. Profile and results are in the Release Evidence Summary.

## Limits
Simulated host; single CPU core shared by load generator and service; in-process calls (no HTTP, TLS or authentication); local file database; synthetic data; one operation only. Results show the behaviour of the data-access layer, not a deployed application.
