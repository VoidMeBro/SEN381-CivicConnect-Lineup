# M3 Technical Debt Register

**Reviewed:** 16 October 2026
**Release scope:** CivicConnect running locally for the SEN381 school project. This register records follow-up work; its open items do not block the approved local release.

| ID | Debt or limitation | Evidence / current state | Follow-up | Priority | Status |
|---|---|---|---|---|---|
| TD-001 | Authentication and sessions were absent from the initial lifecycle slice. | The integrated M3 app now includes sign-in, signed sessions and role checks in `docs/member1_m2/product/serve.py` and `web.py`; covered by web-security tests and CI. | Keep the local secrets private and preserve the existing role/ownership tests. | Low | Addressed for M3 local release |
| TD-002 | The initial reference slice had no web interface. | The integrated M3 app provides a server-rendered web interface in `docs/member1_m2/product/web.py`. | None for the approved local scope. | Low | Addressed |
| TD-003 | The initial slice did not include staff and management request views. | Staff queues and management summaries are implemented and covered by feature and end-to-end tests. | Extend only if the approved school-project scope changes. | Low | Addressed for M3 local release |
| TD-004 | SQLite schema changes are handled by application initialization rather than a general migration framework. | `docs/member1_m2/product/schema.sql` and lifecycle initialization. | Add formal versioned migrations if the schema evolves beyond the current project. | Medium | Open; follow-up |
| TD-005 | SQLite uses a single local database file and serializes writes. | Lifecycle implementation and local performance evidence. | Reassess only if a larger deployment or concurrent-write requirement is introduced. | Low | Accepted for local scope |
| TD-006 | Operational logging and monitoring are limited. | The school-project build is run locally; no monitoring service is configured. | Add operational monitoring only if the project scope later includes hosted operation. | Low | Accepted for local scope |
| TD-007 | Environment configuration is supplied through process variables. | `.env.example` documents variable names; `serve.py` reads environment variables and does not auto-load `.env`. | Follow the README and supply secrets locally; do not commit them. | Low | Addressed/documented |
| TD-008 | Local test history includes more than one Python version. | Member 2 recorded a Python 3.15.0 local run; GitHub Actions passed on the configured Python 3.12 runtime. | Use Python 3.12 for the documented baseline and repeat CI when code changes. | Low | Recorded |
| TD-009 | Lifecycle history has no pagination. | Current local datasets and project demonstration do not require paging. | Add paging if larger datasets or a network API become part of scope. | Low | Accepted for local scope |
| TD-010 | PED and supporting requirement evidence are maintained as versioned documents. | PED v3.0 and the M3 evidence files are included in this documentation change. | Review the linked evidence whenever implementation or scope changes. | Low | Addressed for M3 package |
| TD-011 | The Member 4 staging harness simulates a local host and tests the lifecycle-service slice. | `staging/README_Staging.md` and the historical JSON reports state this boundary. | No follow-up is needed for a local school demonstration; use the integrated app README for the actual M3 run. | Low | Accepted for local scope |
