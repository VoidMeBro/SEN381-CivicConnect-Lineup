# Risk Register - M3 release update (Member 4)

Continues PED Section 11 (R-01 to R-09) and Section 30 (R-10 to R-18). Existing wording is not rewritten; this file records the M3 status change, the evidence for it, and new release risks. Ratings are Member 4's assessment of the release candidate and need team confirmation. Evidence paths are relative to the pack root.

Release candidate assessed: RC-M3-candidate-8bf449ede114 (fingerprint of product/lifecycle.py, product/schema.sql, product/demo.py; documented commit 214e47d32df5fcd5543e22217a48ca5214370400, to be confirmed by Member 1).

## Updates to existing risks

| ID | Previous | M3 status | Evidence and reason |
|---|---|---|---|
| R-08 Citizen data exposure | Medium/High, Active | Active, reduced at service level only | evidence/staging_verification.json ST-05 to ST-08: cross-citizen read, wrong-department staff, citizen transition and deactivated staff all denied on the deployed copy. There is no web/API layer or authentication, so access control over a real interface is unverified. |
| R-09 Deployment blocked by hosting access, quotas or costs | Medium/High, Active | Active, partly reduced | Clean install from the release files into an isolated staging root succeeded (staging/deploy_staging.py). No real host, quota or cost was tested; staging is simulated. |
| R-12 Partial lifecycle save | Medium/High, Active | Reduced, keep open until RC tests are reviewed | ST-03, ST-04, ST-10, ST-11: committed state survives a process restart, stale writes are refused, a refused rejection leaves no record. 20 lifecycle tests were already passing (evidence/verification.txt). |
| R-13 Dependency cannot run in target environment | Medium/High, Active | Reduced | Release runs on Linux, Python 3.12.3, SQLite 3.45.1 with no third-party packages. The M2 evidence was recorded on Windows, Python 3.12.14, SQLite 3.53.1. Applies to this slice only; any framework added later reopens it. |
| R-15 Quota or single database failure | Medium/High, Active | Active, partly reduced | ST-13: SQLite online backup restored to a scratch copy with integrity_check ok and matching row counts. Hosting quotas, backup scheduling and recovery time were not tested. |
| R-18 Reference slice treated as production-ready | Medium/High, Active | Active and confirmed | The release evidence confirms the limits R-18 describes. It is now the main driver of the NOT READY recommendation (RES Section 9). |

## New risks

| ID | Risk and cause | Prob. | Impact | Priority | Mitigation | Contingency | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| R-19 | Core Must Have functions are absent at the release candidate: registration/login, request submission, validation, categories, staff queue/search, administration and management reporting (FR-01, 02, 04, 06, 07, 09, 10, 11, NFR-01) have no implementation. | High | High | Critical | Member 1 delivers the M3 core scope through reviewed PRs; RTM updated per requirement; release decision re-run on the new RC. | Re-baseline scope through change control with explicit deferral rationale; release only the evidenced lifecycle path as a limited demonstration. | Member 1 / team | Open |
| R-20 | Release evidence from Members 1 to 3 (RC tag, CI run, quality gate, security scan, M3 test results, updated RTM, PR approvals) was not available to Member 4, so the summary cannot confirm those areas. | High | High | Critical | Attach each member's evidence to the RES evidence table with commit/run identifiers before submission. | Mark the unsupported area Not Evidenced and keep the recommendation at NOT READY. | Member 4 / all | Open |
| R-21 | Performance evidence is not representative of a deployed application: in-process calls, load generator on the same single-core host, local file database, no HTTP, TLS or authentication. | High | Medium | High | State limits beside every number; repeat against the real stack once an API exists. | Treat NFR-03 as partially evidenced only. | Member 4 | Open |
| R-22 | Staging is simulated, so availability (NFR-04), hosting limits, TLS, process supervision and monitoring are unverified. | High | Medium | High | Document the gap; deploy the same release folder layout to a real host when one is chosen. | Keep NFR-04 Not Yet Implemented. | Member 4 / Member 3 | Open |
| R-23 | Release candidate identity is ambiguous: no tag was supplied, the PED, RTM and evidence name commit 214e47d and revision 4cf9b3c, and later work will move main. Evidence could point to different revisions. | Medium | High | High | Member 1 records one RC tag; every artefact quotes the tag and the fingerprint; re-run staging scripts on the tagged tree. | Re-run deployment and verification and refresh the evidence before submission. | Member 1 / Member 4 | Open |
| R-24 | Documentation defects (DEF-001, DEF-002) reduce confidence in the evidence pack. | Medium | Low | Low | Fix in the next documentation commit. | Accept as minor. | Member 4 | Open |
