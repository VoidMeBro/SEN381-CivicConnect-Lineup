# AI Usage Register - M3 additions (Member 4)

Continues AI-001 to AI-003 (PED Sections 16 and 23) and AI-M2-001 to AI-M2-003. AI output is not authoritative evidence; each entry needs a named human to verify it before it is treated as approved.

| Field | AI-M4-001 |
|---|---|
| Date | 2026-10-15 |
| Student | Member 4 (Jacobus Petrus Geldenhuys per PED team table) |
| Tool | Claude (Anthropic), chat interface with a code-execution sandbox |
| Engineering task | Staging, performance and release evidence for the M3 release candidate |
| AI contribution | Read the uploaded PED v2.0.2 and M2 pack; wrote staging/deploy_staging.py, verify_staging.py and load_test.py; ran the existing validator, 35 tests, the staging checks and the load test in the sandbox; drafted the four registers, the Release Evidence Summary and PED v3.0 Sections 39 to 44. |
| What was run by the tool | Python 3.12.3 on Linux, SQLite 3.45.1, one CPU core, 4 GB RAM, no network. Raw outputs are in evidence/. |
| Verification | PENDING HUMAN VERIFICATION. A team member must re-run the three staging scripts on their own machine, compare the numbers in evidence/ with the numbers in the RES and PED, and check each risk, defect and debt entry against the file it cites. |
| Decision | Draft for team review. Not baselined evidence until the verification record below is completed. |
| Issues found | The sandbox is not the team's staging host; numbers are from a simulated environment. Members 1 to 3 evidence was not available to the tool. RC commit identity could not be confirmed from the files supplied. |

| Verification item | Check required | Status |
|---|---|---|
| Staging scripts | Re-run deploy_staging.py, verify_staging.py and load_test.py; confirm 13/13 and the load figures are reproducible within normal variation | Pending |
| RC identity | Confirm the tag or commit that Member 1 names matches the fingerprint in release.json | Pending |
| Register entries | Confirm every entry's evidence path exists and says what the entry claims | Pending |
| Recommendation | Team agrees the NOT READY recommendation or records a different decision with reasons | Pending |
| Human record | Named reviewer, date and revision recorded here | Pending |
