# Defect Register - M3 release candidate (Member 4)

Defects found by Member 4 while deploying and verifying the release candidate. IDs continue the stable-identifier rule in PED Section 17.2 and must be merged with Member 2's test-defect entries. Severity: High blocks release, Medium needs a fix or accepted workaround, Low is cosmetic or documentation.

| ID | Found in | Description | Severity | Requirement | Found by | Status | Evidence |
|---|---|---|---|---|---|---|---|
| DEF-001 | PED v2.0.2 Section 10 | Heading numbered "1.5 Security Constraints" in a section whose siblings are 10.1 to 10.6. Should be 10.5. | Low | NFR-06 | Document review | Open (fix in PED v3.0 review) | PED Section 10 heading list |
| DEF-002 | README.md | The en dash in "Members 2-4" is stored as mojibake characters (UTF-8 bytes decoded as Windows-1252 and saved again). | Low | NFR-06 | Text scan of the pack | Open | README.md line 21 |
| DEF-003 | product/lifecycle.py | A non-string reference or assignee (for example a list) raises a raw sqlite3.ProgrammingError instead of a Forbidden or InvalidTransition domain error. The transaction rolls back, so no data is changed. 3 of 13 malformed inputs behaved this way; the other 10 returned domain errors. Reachable only if a caller passes untyped values, so a typed API layer would mask it. | Low | FR-13, FR-07 | Robustness probe (staging/robustness_probe.py) | Open | evidence/robustness_probe.json |

## Result of the staging and performance runs

The 13 staging checks (evidence/staging_verification.json) and the NFR-03 load run (evidence/perf_nfr03_profile.json) raised no functional or performance defects. This does not mean the release is defect-free: the checks exercise only the lifecycle service.

## Known gaps recorded as risks, not defects

Unimplemented Must Have requirements are scope gaps and are tracked as R-19, not as defects.
