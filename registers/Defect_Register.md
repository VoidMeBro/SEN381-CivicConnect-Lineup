# M3 Defect Register

**Reviewed:** 16 October 2026. The team reviewed the integrated M3 test and CI evidence. No High- or Medium-severity defect is recorded against the tested local M3 application. The following low-severity findings are retained with their original scope.

| ID | Finding | Severity | Scope | Status | Evidence / disposition |
|---|---|---|---|---|---|
| DEF-001 | PED heading `1.5 Security Constraints` should be `10.5`. | Low | Original PED baseline | Fixed in `CivicConnect_PED_v3.0.docx`; the v2.0 baseline is preserved unchanged. | PED v3.0 Section 10.5 |
| DEF-002 | Mojibake dash recorded in the README inside the preserved M2 evidence pack. | Low | Archived M2 pack only | Retained as a legacy-pack finding; it is not in the current root M3 README. | Legacy pack README review |
| DEF-003 | A list used as a request reference or assignee raised a raw SQLite programming error in three malformed-input cases. | Low | Separate three-file lifecycle-slice probe | Retained as a finding about that slice. The integrated M3 web form accepts text inputs and its current web-security tests passed; the slice result is not reported as an M3 web defect. | `evidence/robustness_probe.json` |

The integrated M3 local test record reports 37 passed, 0 failed and 0 errors. The shared GitHub Actions workflow also passed on main commit `8751bdfabc4535a1aeb060e34d9fe2f5ce1d8659` in run [38870644636](https://github.com/VoidMeBro/SEN381-CivicConnect-Lineup/actions/runs/38870644636). Those results apply to their recorded checks and do not claim that untested behavior is defect-free.
