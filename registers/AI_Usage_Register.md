# AI Usage Register M3 Additions

This entry continues the earlier AI-001 to AI-003 and AI-M2-001 to AI-M2-003 records. AI output is supporting material; the team is responsible for reviewing and approving the engineering evidence and decisions.

| Field | AI-M4-001 |
|---|---|
| Date | 2026-10-15; team review recorded 2026-10-16 |
| Student | Member 4 (Jacobus Petrus Geldenhuys, per the PED team table) |
| Tool | Claude (Anthropic), chat interface with a code-execution sandbox |
| Engineering task | Prepare staging, performance, register and release evidence for M3. |
| AI contribution | Drafted the staging scripts, test reports, four registers, release summary and PED Sections 39–44. The scripts and reports were generated against the three-file lifecycle-service reference slice. |
| Tool execution environment | Python 3.12.3, SQLite 3.45.1, Linux sandbox, one CPU core, 4 GB RAM, no network. Original outputs remain in `evidence/`. |
| Human verification | All four team members confirmed on 2026-10-16 that the integrated M3 application, planned requirements, tests, checks and supporting evidence were tested, checked and verified, and completed the required approvals. They also reran the staging and load checks and confirmed their recorded results for the lifecycle slice. |
| Team decision | On 2026-10-16 the team approved readiness for the M3 school-project release and local demonstration. |
| Boundaries recorded | The approved release is a local school-project application. The lifecycle-slice experiment is simulated and does not include the integrated web application; its recorded measurements apply only to that slice. Public hosting and production operations are outside the approved scope. |

## Verification record

| Item | Status on 2026-10-16 |
|---|---|
| Staging and load reports | Verified by all four team members for the separate lifecycle-service slice; see `evidence/staging_verification.json` and `evidence/perf_nfr03_profile.json`. |
| Integrated application and test evidence | All four team members confirmed the planned M3 requirements, tests, checks and supporting evidence were tested, checked and verified. The recorded local regression run reports 37 passed, 0 failed and 0 errors; see `docs/member1_m2/evidence/team-release-verification.md`. |
| CI | Successful on `main` commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659`; run [38870644636](https://github.com/VoidMeBro/SEN381-CivicConnect-Lineup/actions/runs/38870644636). |
| Candidate identity | Integrated application revision identified by full `main` commit SHA `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659`. The lifecycle-slice report retains its own distinct fingerprint. |
| Register and recommendation review | Team reviewed the M3 registers and approved the scoped academic-submission/demo readiness decision on 2026-10-16. |
