# CivicConnect final demonstration and defence guide

## Team presentation plan

**Target duration:** approximately 24 minutes, followed by individual questions. The brief allocates roughly 6 minutes to the final product, 6 to scope, 4 to M3 closure, 4 to evidence, and 4 to conclusions.

| Segment | Time | Lead | What to show |
|---|---:|---|---|
| Purpose and release identity | 1 min | Team | CivicConnect, assessed baseline SHA, local-only boundary. |
| Final product journey | 5 min | Assigned product demonstrator | Citizen submits and views a request, staff processes it, management views the report. Use synthetic demo accounts only. |
| M1 scope and final delivery | 6 min | Requirements lead | Final RTM and 80% calculation. Explain NFR-01 as an unmet Must Have and NFR-03 as partial. |
| M3 issues and final release decision | 4 min | Release/evidence lead | Nine staging checks passed; load profile failed its reliability gate; explain production no-go. |
| Final evidence and project conclusion | 4 min | Evidence lead | RTM links, CI result, known limitations, next work. |
| Team conclusion | 4 min | All | Stakeholder value, decisions, learning and future work. |

## Product demonstration sequence

1. State the exact assessed application baseline and explain that it is a local academic demonstration.
2. Sign in as a synthetic citizen, submit a valid request and show the reference.
3. Show the citizen request history and current status.
4. Sign in as staff, locate and process the request through an allowed transition.
5. Show the citizen-facing lifecycle explanation.
6. Sign in as management and show the service summary.
7. State that this demonstration does not prove production readiness or the unmet usability and availability criteria.

## Evidence to keep open

- `Final_RTM.csv` and `Scope_Completion.csv`.
- `docs/member1_m2/evidence/member2-test-results.txt` and `team-release-verification.md`.
- GitHub Actions run 38870644636 on application commit 8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659.
- `evidence/website-stage-20261016/staging_load_report.md` and `.json`.
- `registers/Risk_Register_M3.md`, `Defect_Register.md`, `Technical_Debt_Register.md` and `AI_Usage_Register.md`.

## Individual defence preparation

Each member should prepare one original M1 commitment and trace it through the source need, requirement, acceptance criterion, design/decision, final implementation, verification and final status. Each member should also explain a consequential engineering decision, the evidence boundary of the relevant test, one remaining limitation and the team's release decision.

Do not claim that all M1 criteria passed. Distinguish test evidence from manual team verification, the integrated web application from the separate lifecycle slice, and local academic demonstration from production deployment.
