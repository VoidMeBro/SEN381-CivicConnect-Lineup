# CivicConnect M3 Release Evidence Summary

**Decision date:** 16 October 2026
**Decision:** **READY for the M3 school-project release and local demonstration.** The approved scope is to run the integrated app locally.

## Candidate and scope

The integrated M3 application is in `docs/member1_m2/product/`. The release candidate application revision is `main` at commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659`. It includes the citizen, staff and management web workflows, authentication and authorization, the lifecycle service, SQLite persistence, and the shared quality workflow. The document changes in this pull request do not change application code.

All four team members confirm that the M3 application, planned requirements, tests and checks were tested, checked and verified, and that approvals were completed on 16 October 2026. The team identified no release blocker for the local school-project scope. M3 work from Members 1, 2 and 3 is in merged pull requests #13, #14 and #16. The supporting staging and load-test JSON in this pack is an additional service-layer experiment against the three-file lifecycle slice named in that evidence; it is not a deployment test of the integrated M3 web application. See [team verification](docs/member1_m2/evidence/team-release-verification.md).

## Evidence

| Area | Evidence and result | Boundary |
|---|---|---|
| Integrated application | M3 product and web UI in `docs/member1_m2/product/`; local run instructions in its README | Local, server-rendered application using SQLite and synthetic data. |
| Regression tests | Member 2 recorded 37 tests passed, 0 failed and 0 errors. The team reviewed the test records and requirement links on 16 October. | The local execution used Python 3.15.0; it is not by itself proof for the Python 3.12 baseline. |
| CI | GitHub Actions run [38870644636](https://github.com/VoidMeBro/SEN381-CivicConnect-Lineup/actions/runs/38870644636) succeeded on `main` commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659`, after PR #16 merged. It ran the repository's configured compile, regression, performance-smoke, Bandit and Gitleaks checks. | Applies to that exact commit. CI success does not prove absence of all defects or satisfy every non-functional requirement. |
| Staging slice | `evidence/staging_verification.json`: all 13 checks passed; whole team reran and verified the staging and load checks on 16 October | Isolated simulated host, synthetic data, lifecycle service only; not the integrated M3 web app or public hosting. |
| Performance | `evidence/perf_nfr03_profile.json`: 6,000 samples, zero failures, p95 0.825 ms for the lifecycle service lookup; team reran and reviewed the result on 16 October | In-process, single host, local SQLite, no HTTP, TLS, authentication, or network. This is not a production capacity claim. |
| Security | Web security regression tests plus the successful CI Bandit and Gitleaks steps | Targeted tests and scanner results have defined coverage; no penetration test or security certification is claimed. |
| Requirement trace | `docs/member1_m2/evidence/requirement-matrix.csv`, `member2-test-traceability.csv`, and `test-strategy.md` | Team checked and verified the planned requirements and supporting evidence. |
| Team approval | All four members completed testing, checks, verification and approval on 16 October 2026. | Ready for the local M3 school-project release and demonstration. |

## Evidence scope

The team confirms all planned M3 requirements and verification checks were tested and verified for the local school-project release. Individual records show the exact test runs and results. The separate staging JSON identifies the lifecycle-slice candidate `RC-M3-candidate-8bf449ede114`; this identifier belongs only to that supplemental service-layer report and is not the integrated M3 application revision.

The final document package is included in this documentation pull request. The integrated application revision remains identified by the full commit SHA above.

## Reproduction

Use the root `README.md` and `docs/member1_m2/product/README.md` to start the integrated M3 application and run its checks. `staging/README_Staging.md` explains the separate, historical lifecycle-slice experiment and its limitations.
