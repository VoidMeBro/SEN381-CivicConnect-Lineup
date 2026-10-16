# CivicConnect Release Evidence Summary (M3, Member 4)

Prepared 15 October 2026. Draft for team verification (see AI-M4-001).

## 1. Recommendation

**NOT READY.**

The release candidate is a verified, working request-lifecycle service, but it is not a releasable application. Nine of the fifteen Must Have requirements have no implementation (FR-01, 02, 04, 06, 07, 09, 10, 11 and NFR-01), there is no web or API layer and no authentication, and the CI, security-scan, M3 test-suite and pull-request evidence from Members 1 to 3 was not available to this summary. The path that does exist behaved correctly in staging and met its performance target by a wide margin.

What would move the decision: see Section 9.

## 2. Release candidate identity

| Item | Value |
|---|---|
| Candidate | M2 reference slice: product/lifecycle.py, product/schema.sql, product/demo.py |
| Staging release id | RC-M3-candidate-8bf449ede114 |
| Fingerprint | SHA-256 over the three release files (recorded in release.json on the staging host) |
| Commit named in the pack | 214e47d32df5fcd5543e22217a48ca5214370400 (Governance.md); document revision 4cf9b3c5e86d63b2fa49e7526fd147ac5d0be767 |
| Tag | None supplied. Member 1 must name the M3 release tag; this summary then needs re-running (R-23). |
| PED | v2.0.2 (hash a745a93c...) is the document this work extends to v3.0 |

## 3. Evidence by area

| Area | Evidence | Result | Limits |
|---|---|---|---|
| Unit and component tests | evidence/verification.txt; 35 tests re-run on Linux, Python 3.12.3, SQLite 3.45.1 | 35 of 35 pass (20 lifecycle, 15 traceability) | Written in M2. Member 2's M3 suite (5 unit, 5 black-box, 3 API, 2 E2E) was not provided. |
| Traceability checks | `traceability.py validate`, `diff`, `verify-manifest` | All three pass; baseline diff empty | Structural checks only; they do not prove evidence truth. |
| CI and quality gate | None provided | Not evidenced | Member 3. |
| Security | Member 4 local scan: no secret-like strings in code, SQL or JSON; no third-party imports in product, staging or tooling code; no credentials or environment secrets required. Service-level access tests ST-05 to ST-08 pass. | Clean for the scan performed | Not a CI scanner, dependency audit or penetration test. No authentication layer exists (TD-001). |
| Staging | evidence/staging_verification.json; staging/ scripts | Clean install, 13 of 13 checks pass | Simulated single host (R-22). |
| Performance | evidence/perf_nfr03_profile.json; evidence/perf_stress_supplementary.json | See Section 5 | In-process, same host, one core, no HTTP (R-21). |
| Robustness | evidence/robustness_probe.json | 10 of 13 malformed inputs gave domain errors; 3 gave a raw sqlite3 error (DEF-003) | Probe of 13 inputs, not a fuzz run. |
| Defects | registers/Defect_Register.md | 3 open, all Low | Members 2 and 3 may add more. |
| Technical debt | registers/Technical_Debt_Register.md | 11 items, 3 High | |
| AI usage | registers/AI_Usage_Register.md | AI-M4-001 pending human verification | |

## 4. Staging

Deployment: `deploy_staging.py` copied the three release files into releases/RC-M3-candidate-8bf449ede114 on an isolated root, verified each copy against the source and against evidence_manifest.json, linked `current`, created the database from the deployed schema and loaded synthetic fixtures. The verification and load scripts import the service from `current`, and check 1 confirms that.

Checks (all pass): release integrity, schema and integrity_check, the critical journey, restart persistence, four unauthorised-access denials, invalid transition, stale write, rejection without and with a reason, backup and restore.

Critical journey (FR-13, FR-05, FR-08): Submitted to Accepted to In Progress to Resolved to Closed. After each commit a separate connection read the citizen's view; the read took under a millisecond each time against targets of 5 seconds (FR-05) and 60 seconds (FR-08), measured at the data layer only. Final history showed four events with versions 1 to 4 in order.

Not verified: registration, submission, staff queue, administration, reporting. They are not in the release candidate.

Environment difference: M2 evidence was recorded on Windows 11, Python 3.12.14, SQLite 3.53.1. Staging ran Linux, Python 3.12.3, SQLite 3.45.1 and passed unchanged.

## 5. Performance

Operation: requester status lookup, `SqliteLifecycleStore.history(actor, reference)`. Chosen because NFR-03 is the only requirement with a numeric load target and this is the only lookup the candidate implements.

Workload (primary run, NFR-03 profile): 50 virtual users, 10,000 stored requests (1,000 citizens, 20 staff, 0 to 4 events per request), one authorised lookup per user every 5 seconds, 60 seconds warm-up discarded, then 600 seconds measured. Each user used its own store instance, so each lookup opened a new connection.

Environment: Linux sandbox, 1 CPU core, 4 GB RAM, Python 3.12.3, SQLite 3.45.1, local file database, load generator threads in the same process as the service.

| Measure | Result | NFR-03 target |
|---|---|---|
| Samples | 6,000 | |
| Failures | 0 (0.0%) | below 1% |
| Median | 0.49 ms | |
| 95th percentile | 0.83 ms | 3 s |
| 99th percentile | 1.25 ms | |
| Maximum | 8.2 ms | |
| Share within 3 s | 100% | at least 95% |

Supplementary headroom run (50 users, no think time, 30 seconds after 5 seconds warm-up): 131,197 lookups, 0 failures, about 4,370 per second, p95 26.6 ms, p99 72.2 ms, maximum 221.7 ms. This shows the data layer is not the likely bottleneck. It is not a capacity claim.

Limitations: the numbers measure the data-access layer, not a deployed application. There is no HTTP, TLS, authentication, rendering or network latency. Generator and service compete for one core. The database holds 10,000 requests, not the 50,000 and 100 users of NFR-07, which stays untested. Only reads were measured; write contention (TD-005) was not. The result supports NFR-03 as "met at the data layer" and nothing stronger.

## 6. Defects

| ID | Summary | Severity | Status |
|---|---|---|---|
| DEF-001 | PED heading "1.5 Security Constraints" should be 10.5 | Low | Open |
| DEF-002 | Mojibake dash in README.md line 21 | Low | Open |
| DEF-003 | Non-string reference or assignee gives raw sqlite3.ProgrammingError, not a domain error; data unchanged | Low | Open |

No functional or performance defects came from the 13 staging checks or the load runs.

## 7. Requirement status at the candidate

From rtm.json: 15 Must Have requirements, of which 6 are In Development (FR-03, FR-05, FR-08, FR-12, FR-13, NFR-02) and 9 are Not Yet Implemented. Should Have: NFR-06 In Development; NFR-03, NFR-04, NFR-05 Not Yet Implemented. Could Have: NFR-07 Not Yet Implemented. No requirement is recorded as accepted. The staging evidence adds support for FR-05, FR-08, FR-13 and NFR-02 at service level and for NFR-03 at data-layer level; Member 2 should link ST-01 to ST-13 and the load results in the RTM.

## 8. Residual risks

Release-blocking: R-19 (core functions absent), R-20 (other members' evidence missing), R-18 (reference slice is not a production application). Material: R-21 (performance not representative), R-22 (simulated staging), R-23 (RC identity), R-08 (no access control over a real interface), R-15 (hosting quotas and recovery untested). Full text and mitigations: registers/Risk_Register_M3.md.

## 9. Conditions to move the decision

CONDITIONALLY READY (limited release of the lifecycle path) would need all of:
1. Member 1 names one release tag and the web or API layer with authentication for at least the citizen submit, history and staff transition journeys, with the other Must Have gaps either implemented or deferred through change control.
2. Member 2's M3 results and updated RTM, with the high-priority requirements linked to passing tests.
3. Member 3's CI run on that tag with the quality gate passing, plus the security or dependency check output, and the two-approval pull-request record.
4. Staging scripts re-run on the tagged tree, ideally on a real host, and the load test repeated through the real interface.

READY would additionally need the Must Have set implemented and verified, or formally deferred with client agreement, and no open High defect.

## 10. How to reproduce

See staging/README_Staging.md. Three commands (deploy, verify, load) with `CIVICCONNECT_ENV=staging`; the full load run takes about 11 minutes.
