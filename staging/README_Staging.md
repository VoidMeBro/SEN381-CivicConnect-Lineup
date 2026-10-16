# Member 4 lifecycle-slice evidence guide

## Which version this checks

These scripts and their JSON results are for the three-file lifecycle-service slice used in the Member 4 staging and load experiment. They do not deploy or test the integrated M3 web application. The team reran and reviewed this slice's 13 staging checks and load profile on 16 October 2026.

For the actual M3 school-project application and local demonstration, follow the repository-root `README.md` and `docs/member1_m2/product/README.md` instead.

## Run the historical lifecycle-slice experiment

The source folder must be an extracted copy of `CivicConnect_Team_PED_Pack.zip` that contains both `evidence_manifest.json` and `product/lifecycle.py`. The staging output folder must be separate from that source folder. Python 3.11 or later is required; the scripts use only the standard library.

PowerShell example, run from the repository root:

```powershell
$source = (Resolve-Path '.test-tmp/CivicConnect_Team_PED_Pack').Path
$env:CIVICCONNECT_ENV = 'staging'
python staging/deploy_staging.py --source $source --env-root "$PWD/.test-tmp/cc-staging"
python staging/verify_staging.py --env-root "$PWD/.test-tmp/cc-staging" --out evidence/staging_verification.json
python staging/load_test.py --env-root "$PWD/.test-tmp/cc-staging" --out evidence/perf_nfr03_profile.json
```

The full profile takes about eleven minutes. It creates synthetic local data under the staging root. The scripts require `CIVICCONNECT_ENV=staging` and should not be pointed at any data used by the M3 application.

## Recorded results and boundaries

- `evidence/staging_verification.json`: 13 of 13 service-slice checks passed.
- `evidence/perf_nfr03_profile.json`: 6,000 service-slice lookup samples, zero failures, p95 0.825 ms.
- `evidence/perf_stress_supplementary.json`: supplementary same-host headroom run.
- `evidence/robustness_probe.json`: 13 malformed-input cases; 10 returned documented domain errors and 3 produced a raw SQLite programming error in this slice.

The load generator and service share one process and host, use a local SQLite file, and do not include a browser, HTTP, TLS, or network path. These figures are supporting engineering evidence for the lifecycle slice only, not a test of the complete M3 application or a claim that every requirement was measured.
