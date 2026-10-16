# AI Usage Register - M3 additions (Member 4)

Continues AI-001 to AI-003 (PED Sections 16 and 23) and AI-M2-001 to AI-M2-003. AI output is not authoritative evidence; each entry needs a named human to verify it before it is treated as approved.

| Field | AI-M4-001 |
|---|---|
| Date | 2026-10-15 |
| Student | Member 4 (Jacobus Petrus Geldenhuys per PED team table) |
| Tool | Claude (Anthropic), chat interface with a code-execution sandbox |
| Engineering task | Staging, performance and release evidence for the M3 release candidate |
| AI contribution | Read the uploaded PED v2.0.2 and M2 pack; wrote staging/deploy_staging.py, verify_staging.py and load_test.py; ran the existing validator, 35 tests, the staging checks and the load test in the sandbox; drafted the four registers, the Release Evidence Summary and PED v3.0 Sections 39 to 44. |
| What was run by the tool | Python 3.12.3 on Linux, SQLite 3.45.1, one CPU core, 4 GB RAM, no network. The original sandbox outputs are in evidence/. |
| Verification | VERIFIED BY THE WHOLE TEAM 2026-10-16: all four team members reran the staging and load checks, confirmed the results, checked the release candidate identity and evidence-register entries, and agreed the NOT READY recommendation. The team reviewed branch revision 7e47231. |
| Decision | Team verification is complete. The release recommendation is NOT READY because the release candidate does not implement all required Must Have capabilities and lacks a real web/API and authentication layer, as detailed in the Release Evidence Summary. |
| Issues found | The original sandbox was simulated, not the team's staging host. Members 1 to 3 evidence was not available to the AI tool during drafting. The team subsequently reviewed and verified the release evidence and checks listed below. |

| Verification item | Check required | Status |
|---|---|---|
| Staging scripts | Re-run deploy_staging.py, verify_staging.py and load_test.py; confirm 13/13 and the load figures are reproducible within normal variation | Verified by the whole team; 2026-10-16 |
| RC identity | Confirm the tag or commit that Member 1 names matches the fingerprint in release.json | Verified by the whole team; 2026-10-16 |
| Register entries | Confirm every entry's evidence path exists and says what the entry claims | Verified by the whole team; 2026-10-16 |
| Recommendation | Team agrees the NOT READY recommendation or records a different decision with reasons | Team agrees NOT READY; verified 2026-10-16 |
| Human record | Whole team (Members 1–4, per PED team table); date and revision checked | 2026-10-16; revision 7e47231 |
