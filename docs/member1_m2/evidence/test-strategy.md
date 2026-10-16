# M3 Verification Strategy

## Scope and evidence boundary

The suite exercises the integrated local CivicConnect M3 application against the supplied Master Project Brief, M3 milestone requirements, Assignment 3 research considerations, and PED functional and quality requirements. All automated data is synthetic. Results apply only to the tested code and stated runtime.

## Test design

| Evidence class | Minimum | Current cases | Techniques / purpose |
|---|---:|---:|---|
| Unit / component | 5 | `test_component.py` (5) | Transition policy, required fields, illegal state, atomic rollback |
| Black-box functional | 5 | `test_blackbox.py` (5) | Equivalence classes and boundary values for title, description, location and category |
| API / integration | 3 | `test_integration.py` (6) plus route tests | Service-to-SQLite commit, authorization, assignment, sorting and date filtering |
| E2E / system | 2 | `test_e2e.py` (4) | Citizen-to-staff-to-management, full lifecycle/requester feedback and unauthorised-action paths |
| Security / feature regression | 15 | `test_features.py` (9), `test_web_security.py` (6) | Roles, ownership, CSRF, HTML escaping, admin bootstrap, reporting and data migration |
| CI / repository tooling | 2 | `test_tools.py` | Verify required CI stages are configured and generated local databases/keys stay outside source evidence |

Overlap between classes is intentional where a case proves a critical path at more than one boundary. `python -m unittest discover -s tests -v` runs the entire suite. CI also compiles sources, runs a small load scenario, runs Bandit static analysis, and scans repository contents for secrets.

## Requirement coverage summary

| Requirement | Implementation evidence | Verification evidence | Result / limitation |
|---|---|---|---|
| Master Brief §3 requester capabilities; FR-01/02/03/07/08/10 | `product/web.py`, `product/lifecycle.py`, `product/schema.sql` | `tests/test_blackbox.py`, `tests/test_web_security.py`, `tests/test_e2e.py`; team verification record | Planned requester workflows and acceptance checks verified by the team for the local school-project scope. |
| Master Brief §3 staff capabilities; FR-04/05/11/12/13 | `product/web.py`, `product/lifecycle.py` | `tests/test_component.py`, `tests/test_integration.py`, `tests/test_web_security.py`, `tests/test_e2e.py` | Department-scoped queue, detail open, controlled lifecycle, assignment and history exercised. |
| Master Brief §3 management; FR-09 | `product/web.py`, `product/lifecycle.py` | `tests/test_features.py`, `tests/test_integration.py`, `tests/test_e2e.py` | Date/category/status report, open/overdue and category/status counts exercised. |
| FR-06 account and role management | `product/web.py`, `product/lifecycle.py` | `tests/test_features.py`, `tests/test_web_security.py` | Admin-only changes and active-account effects exercised. |
| NFR-02 privacy/access | Server-side access checks in `product/lifecycle.py` and `product/web.py` | `tests/test_web_security.py` | Cross-citizen and role-denial checks pass for exercised routes; does not prove all possible attack paths. |
| NFR-03 performance | `product/performance_smoke.py` | CI workload step | 10,001 synthetic records and 50 simultaneous one-time lookups; not the PED's ten-minute repeated workload. |
| NFR-04 availability | Local school-project scope and team verification record | Team review and verification of planned M3 requirements/checks | Verified for the agreed local demonstration scope; hosted availability is outside scope. |
| NFR-05 data quality | Server validation and active category lookup | `tests/test_blackbox.py`, `tests/test_features.py` | Boundary and invalid-category cases exercised. |
| NFR-06 traceability | PED v3.0, requirement matrix, test traceability, and this strategy | CI and test suite | Supporting M3 code/test links are recorded; test-derived criteria are identified as such. |
| NFR-07 scale | Indexed SQLite schema; integrated performance smoke check; team verification record | CI performance-smoke step and team verification | Planned M3 performance checks were verified for the local school-project scope. The individual smoke record retains its stated dataset and workload. |

## Reproduction

From `docs/member1_m2`. The local Member 2 test execution on 13 October 2026 used Python 3.15.0. The shared GitHub Actions workflow uses Python 3.12; the successful main-branch run below supplies the baseline CI result.

```powershell
python -m compileall -q product tests
python -m unittest discover -s tests -v
python product/performance_smoke.py
```

The GitHub Actions workflow installs Bandit, runs it over `product/` (excluding assertion-only demo checks), and runs Gitleaks against the checked-out repository. The workflow passed on main commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659` in run [38870644636](https://github.com/VoidMeBro/SEN381-CivicConnect-Lineup/actions/runs/38870644636). Scanner results are evidence for that commit and do not prove that every vulnerability is absent.

## Member 2 local test execution

Execution date: 13 October 2026

Environment: Windows, Python 3.15.0

Command:
`python -m unittest discover -s tests -p "test_*.py" -v`

Results:
- Total tests: 37
- Passed: 37
- Failed: 0
- Errors: 0
- Execution time: 9.439 seconds

Evidence: `evidence/member2-test-results.txt`

During initial execution, six tests failed because the local Python environment lacked the `tzdata` dependency. After installing the dependency, the remaining repository tooling test failed because it scanned the local `.venv` directory. The test was updated to exclude `.venv` from the source-file scan.

After these changes, the full suite passed. GitHub Actions subsequently passed on the integrated M3 main revision above. On 16 October 2026, all four team members confirmed that the integrated application and planned M3 requirements, tests, checks and supporting evidence were tested, checked and verified, and completed the required approvals for the local school-project release. The agreed scope is local use and demonstration; hosted production operations are outside scope. See `team-release-verification.md`.
