# Release Evidence Summary

## Candidate and decision

Candidate: `feat/m3-member1-civic-workflow` branch under review. The release commit identifier will be recorded after the final change is committed. This is a student-scale integrated release candidate for local demonstration; it is not a production release and no defect-free claim is made.

**Readiness decision: conditionally suitable for a controlled local demonstration after the listed checks pass on the final commit. Not ready for production deployment.** The decision is limited to exercised behavior, synthetic local data and the stated test environment.

## Evidence

| Area | Evidence / current state |
|---|---|
| Build / syntax | Python `compileall` over `product` and `tests` |
| Functional and integration regression | 35 meaningful cases: 5 component, 5 black-box, 6 integration, 2 E2E, 15 feature/security regression and 2 repository tooling checks. Local full suite passed on 2026-10-13. |
| Security verification | Route-level role/ownership/CSRF/XSS/bootstrap tests; Bandit static scan and Gitleaks secret scan configured in `.github/workflows/quality.yml` |
| Performance | `product/performance_smoke.py`: 10,001 rows and 50 concurrent one-time lookups; latest local run observed p95 12.9 ms with zero failures. This is not the full ten-minute NFR-03 workload. |
| Simulated staging | [simulated-staging.md](simulated-staging.md): isolated local database, synthetic accounts, and reproduction steps |
| Requirement trace | [test-strategy.md](test-strategy.md): Master §3 and FR/NFR links to implementation and tests |

## Blockers and residual limits

- GitHub Actions results and hosted scanner findings must be checked for the final pushed commit; local configuration alone is not CI evidence. Bandit is not installed in the local bundled runtime, so its local scan was not executed.
- The current test suite does not include a five-person usability study, the full ten-minute NFR-03 workload, the 50,000-row/100-user NFR-07 scenario, or the NFR-04 20-weekday availability probe.
- No hosted staging URL, TLS deployment, backup/restore rehearsal, production rollback or operational monitoring evidence is present.
- The maintained PED v3.0, RTM, risk/defect/technical-debt/AI registers and sign-off need to be updated by continuing the authoritative project source documents. This branch has an earlier PED copy and a packaged M2 evidence set, so it does not silently replace that baseline with a duplicate.
- Two independent reviewers must approve the precise pull-request commit before merge. This summary does not represent team or assessor approval.

## Progression conditions

Use the final commit recorded on the existing pull request. Require the CI workflow and scanners to complete successfully, resolve or explicitly triage findings, update the controlled PED/RTM and project registers, attach the assessor-accessible staging instructions, and record authorized team review. Reassess production readiness separately after deployment, recovery and availability evidence exists.
