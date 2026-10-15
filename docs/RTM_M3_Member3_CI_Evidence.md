# RTM M3 Evidence — Member 3 (CI and Configuration)

This file records the CI and configuration evidence that supports the Requirements Traceability Matrix for M3. Member 2 can merge these rows into the main RTM.

## Evidence Source

- CI workflow: `.github/workflows/quality.yml`
- CI run URL: https://github.com/VoidMeBro/SEN381-CivicConnect-Lineup/actions/runs/38795183332
- Repository: https://github.com/VoidMeBro/SEN381-CivicConnect-Lineup
- Branch: feat/m3-member3-repo-ci-config
- Commit: acfea77

## RTM Evidence Rows

| Requirement | Acceptance Criteria | Implementation | Test / Verification Evidence | CI Evidence | Status |
|---|---|---|---|---|---|
| FR-13 Controlled transitions | Permit Submitted to Accepted or Rejected; Accepted to In Progress; In Progress to Resolved; Resolved to Closed. Only authorised staff transition records. | RequestLifecycleCoordinator / LifecyclePolicy / SqliteLifecycleStore in product/lifecycle.py | tests/test_lifecycle.py — transition and authorisation tests | CI workflow runs test suite on every PR and push | In Development |
| FR-05 Update status and remarks | A permitted update saves status, remark, actor and timestamp. | SqliteLifecycleStore in product/lifecycle.py | tests/test_lifecycle.py — update and persistence tests | CI workflow runs test suite on every PR and push | In Development |
| NFR-02 Access control | A user with the Citizen role cannot view another citizen's submissions. | Ownership checks in transition and history methods | tests/test_lifecycle.py — negative access tests | CI workflow runs test suite on every PR and push | In Development |
| NFR-06 Maintainability | Each baselined requirement can be traced to source, criteria, and evidence. | RTM structure in rtm.json | tests/test_traceability.py — RTM structure tests | CI workflow verifies RTM structure on every PR and push | In Development |
| Security (constraint) | Credentials must not be committed to source control. | `.gitignore` excludes `.env`. `.env.example` documents required variables. | CI secrets detection step scans for hardcoded credentials | CI workflow runs secrets detection on every PR and push | In Development |
| Configuration (constraint) | Configuration must be documented and separated from code. | `.env.example` documents `DATABASE_PATH`, `LOG_LEVEL`, `APP_ENV` | CI configuration verification step confirms `.env.example` exists | CI workflow runs configuration check on every PR and push | In Development |

## How to Read This Evidence

Each row links a requirement to:
- The acceptance criterion it addresses
- The implementation that satisfies it
- The test or verification method
- The CI evidence that runs automatically

The CI workflow provides continuous verification. Every time code is pushed or a pull request is opened, the CI runs the tests and checks. If any check fails, the PR is blocked from merging.

## What This Evidence Does Not Prove

The CI evidence proves that the automated checks pass for the tested revision. It does not prove that the application is free of defects, that it will perform under load, or that every acceptance criterion is fully satisfied. Those claims require complementary evidence such as staging deployment, performance testing, and manual validation.
