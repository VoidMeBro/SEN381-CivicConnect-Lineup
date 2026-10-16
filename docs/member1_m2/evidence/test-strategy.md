# M3 Verification Strategy

## Scope and evidence boundary

The suite exercises the implemented local CivicConnect release candidate against the supplied Master Project Brief, M3 milestone requirements, Assignment 3 research considerations, and approved M2/PED functional and quality requirements. All data in automated runs is synthetic. Results apply only to the exact tested checkout and local runtime described in the recorded command output.

## Test design

| Evidence class | Minimum | Current cases | Techniques / purpose |
|---|---:|---:|---|
| Unit / component | 5 | `test_component.py` (5) | Transition policy, required fields, illegal state, atomic rollback |
| Black-box functional | 5 | `test_blackbox.py` (5) | Equivalence classes and boundary values for title, description, location and category |
| API / integration | 3 | `test_integration.py` (6) plus route tests | Service-to-SQLite commit, authorization, assignment, sorting and date filtering |
| E2E / system | 2 | `test_e2e.py` (2) | Citizen-to-staff-to-management and full lifecycle/requester feedback paths |
| Security / feature regression | 15 | `test_features.py` (9), `test_web_security.py` (6) | Roles, ownership, CSRF, HTML escaping, admin bootstrap, reporting and data migration |
| CI / repository tooling | 2 | `test_tools.py` | Verify required CI stages are configured and generated local databases/keys stay outside source evidence |

Overlap between classes is intentional where a case proves a critical path at more than one boundary. `python -m unittest discover -s tests -v` runs the entire suite. CI also compiles sources, runs a small load scenario, runs Bandit static analysis, and scans repository contents for secrets.

## Requirement coverage summary

| Requirement | Implementation evidence | Verification evidence | Result / limitation |
|---|---|---|---|
| Master Brief §3 requester capabilities; FR-01/02/03/07/08/10 | `product/web.py`, `product/lifecycle.py`, `product/schema.sql` | `tests/test_blackbox.py`, `tests/test_web_security.py`, `tests/test_e2e.py` | Local register, submit, own history, active category, validation and status feedback exercised. No usability study with five representative users. |
| Master Brief §3 staff capabilities; FR-04/05/11/12/13 | `product/web.py`, `product/lifecycle.py` | `tests/test_component.py`, `tests/test_integration.py`, `tests/test_web_security.py`, `tests/test_e2e.py` | Department-scoped queue, detail open, controlled lifecycle, assignment and history exercised. |
| Master Brief §3 management; FR-09 | `product/web.py`, `product/lifecycle.py` | `tests/test_features.py`, `tests/test_integration.py`, `tests/test_e2e.py` | Date/category/status report, open/overdue and category/status counts exercised. |
| FR-06 account and role management | `product/web.py`, `product/lifecycle.py` | `tests/test_features.py`, `tests/test_web_security.py` | Admin-only changes and active-account effects exercised. |
| NFR-02 privacy/access | Server-side access checks in `product/lifecycle.py` and `product/web.py` | `tests/test_web_security.py` | Cross-citizen and role-denial checks pass for exercised routes; does not prove all possible attack paths. |
| NFR-03 performance | `product/performance_smoke.py` | CI workload step | 10,001 synthetic records and 50 simultaneous one-time lookups; not the PED's ten-minute repeated workload. |
| NFR-04 availability | Not measured in this local candidate | None | 20 weekday one-minute probe target remains unverified. |
| NFR-05 data quality | Server validation and active category lookup | `tests/test_blackbox.py`, `tests/test_features.py` | Boundary and invalid-category cases exercised. |
| NFR-06 traceability | This index and M2 source package | CI and test suite | Code/test links recorded here; full controlled PED v3/RTM integration awaits the maintained source PED's owner. |
| NFR-07 scale | Indexed SQLite schema | Load script at 10,001 rows / 50 users | 50,000 rows / 100 concurrent and the longer pattern remain unmeasured. |

## Reproduction

From `docs/member1_m2` with Python 3.12:

```powershell
python -m compileall -q product tests
python -m unittest discover -s tests -v
python product/performance_smoke.py
```

The GitHub Actions workflow installs Bandit, runs it over `product/` (excluding assertion-only demo checks), and runs Gitleaks against the checked-out repository. A clean scanner result is bounded evidence, not proof that vulnerabilities are absent. The current offline execution did not include CI-hosted scanner results.
