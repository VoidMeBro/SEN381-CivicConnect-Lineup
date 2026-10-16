# M3 Release Evidence Summary

**Decision date:** 16 October 2026
**Decision:** **READY for the M3 school-project release and local demonstration.** The approved scope is to run the integrated app locally.

## Candidate identity

The integrated M3 application is in `docs/member1_m2/product/`. Its reviewed software revision is `main` commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659`. All four team members confirmed that the planned requirements, tests, checks and evidence were tested, checked and verified, and completed the required approvals on 16 October 2026. The application revision is identifiable by its full commit SHA; no release tag is claimed. See `team-release-verification.md`.

The root `evidence/` reports and `staging/` scripts in the Member 4 contribution are a separate lifecycle-service experiment against a three-file reference slice. They are not deployment or load-test results for the integrated M3 web application.

## Evidence

| Area | Evidence and result | Boundary |
|---|---|---|
| Application | M3 citizen, staff and management workflows, web UI, authentication, authorization, lifecycle service and persistence in `product/` | Local application using SQLite and synthetic data. |
| Automated regression | Member 2's final local run: 37 passed, 0 failed, 0 errors; team reviewed the test records and links on 16 October | Local run used Python 3.15.0. The hosted CI run supplies the Python 3.12 workflow result. |
| CI and scanners | [GitHub Actions run 38870644636](https://github.com/VoidMeBro/SEN381-CivicConnect-Lineup/actions/runs/38870644636) succeeded on `main` commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659`, after PR #16 merged | Result applies to that exact commit and configured checks; it is not proof of zero defects. |
| Team-verified staging slice | `../../../evidence/staging_verification.json`: 13 of 13 checks passed; staging and load results reviewed by all four team members on 16 October | Simulated, single-host lifecycle service only; not integrated web staging. |
| Performance | `../../../evidence/perf_nfr03_profile.json`: 6,000 samples, zero failures, p95 0.825 ms; team reviewed the run on 16 October | Measures in-process SQLite lookup on one host; no HTTP, TLS, authentication layer or network. |
| Security | Web security regression tests and successful Bandit/Gitleaks CI steps | No penetration test or security certification is claimed. |
| Traceability | `requirement-matrix.csv`, `member2-test-traceability.csv`, and `test-strategy.md` | The team checked and verified the planned M3 requirements and evidence for the local school-project scope. |

## Scope and release boundaries

The team verified the planned M3 requirements and checks for the agreed local school-project scope. Public hosting, hosted availability, TLS operations, production rollback and a public launch are outside that scope. Individual evidence records retain their actual measurements and execution boundaries: for example, the staging JSON identifies `RC-M3-candidate-8bf449ede114`, the three-file lifecycle slice, and is not the integrated M3 application revision. These evidence boundaries do not change the team's release decision for the local application.

## Reproduction

For the integrated application, follow the repository-root `README.md` and `../product/README.md`. For the separate lifecycle-slice experiment, see the root `staging/README_Staging.md`.
