# M3 Risk Register Update

**Reviewed by the team:** 16 October 2026. This update assesses the integrated M3 application identified by `main` commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659`. The root `staging/` scripts and JSON reports concern a separate lifecycle-service slice and are not evidence for the integrated M3 application.

## M3 status updates

| ID | Risk | Current status | Evidence and treatment |
|---|---|---|---|
| R-08 | Citizen data exposure | Reduced for exercised local application paths; remains open for production | M3 provides authentication, sessions and role/ownership checks. The web security tests and CI passed. No penetration test or hosted security assessment is claimed. |
| R-09 | Hosting access, quotas or costs prevent deployment | Outside the approved local school-project scope | No hosting account or quota evaluation is recorded; the project is run locally. |
| R-12 | Partial lifecycle save or stale update | Reduced for the tested M3 scope | Transactional lifecycle tests, integration tests, restart checks in the separate slice and the successful main CI run provide evidence for exercised paths. |
| R-13 | Runtime or dependency incompatibility | Reduced; retain as a maintenance risk | GitHub Actions passed on the configured Python 3.12 runtime. A local test record also used Python 3.15. No dependency or runtime guarantee beyond the recorded environments is claimed. |
| R-15 | Data loss or database failure | Partly reduced; open for hosted operations | The lifecycle-slice staging experiment restored a SQLite backup successfully. No scheduled production backups, host quotas or recovery-time rehearsal are evidenced. |
| R-18 | Reference slice mistaken for a production application | Mitigated for this submission | The PED and release summaries distinguish the integrated M3 application from the lifecycle-slice experiment and explicitly limit the decision to academic submission/local demo. |

## M3 risks added or revised

| ID | Risk | Probability | Impact | Priority | Mitigation / follow-up | Status |
|---|---|---|---|---|---|---|
| R-19 | Planned usability requirement/checks for local school-project scope. | Medium | Medium | Medium | Team verification recorded 2026-10-16; revisit only if scope expands. | Verified for agreed scope; no local-release blocker. |
| R-20 | Hosted availability, TLS, monitoring and hosting limits are not demonstrated (NFR-04). | Low for current scope | Low | Low | No action for the approved local-only school-project release. | Accepted outside current scope. |
| R-21 | Planned performance requirements/checks for local school-project scope. | Medium | Medium | Medium | Team verification recorded 2026-10-16; individual evidence records retain their workload boundaries. | Verified for agreed scope; no local-release blocker. |
| R-22 | The Member 4 staging harness tests a simulated lifecycle-service slice, not the integrated M3 web application. | Medium | Low | Low | Keep the limitation beside each result; use the integrated app's local instructions for the school-project demo. | Accepted for current local scope. |
| R-23 | Evidence can drift if readers confuse the app commit and the lifecycle-slice fingerprint. | Low | Medium | Medium | Identify the integrated M3 revision by full commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659` and retain the separate slice ID only with its historical evidence. | Mitigated; team reviewed 2026-10-16. |
| R-24 | Evidence documents may drift from the application as later changes are made. | Medium | Medium | Medium | Keep the PED, RTM, registers and release summary in the reviewed documentation PR; re-check commit IDs and CI results for subsequent changes. | Open; routine document control. |

## Release decision

The team approved readiness for the M3 school-project release and local demonstration on 16 October 2026. R-19 and R-21 are verified for the agreed local project scope. R-20 concerns hosted operations outside scope; R-22 records the separate staging slice boundary. None blocks local release.
