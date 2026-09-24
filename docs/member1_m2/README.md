# Member 1 M2 delivery

I approve this Member 1 M2 document and the decisions recorded in it. Our four-member allocation and M1 sign-off are confirmed. The current PED is v2.0.1; the approved v2.0 source is preserved unchanged in baselines.

Open CivicConnect_PED_v2.0_Member1.docx for the PED, RTM.html for live requirement lookup, Member1_Completion_Checklist.md for the ten responsibilities, and Presentation.md for my demonstration script. ADRs.md records the approved decisions drawn from M1 and Assignment 2.

## Run the traceability checks

Python 3.11 or later; no external packages, credentials, database or network are required.

```powershell
python traceability.py validate
python traceability.py diff
python traceability.py verify-manifest
python -m unittest discover -s tests -v
python traceability.py render
```

The validator checks all 20 requirements, required fields, controlled implementation statuses, local evidence paths and exact matching approved change records. The manifest checks evidence hashes. The HTML view is generated from rtm.json. Approval and implementation are separate fields.

Member_Handoff.md contains the single consolidated list of incoming Members 2–4 M2 artefacts. The approved product trace is designed from M1 and A2; its execution evidence will be attached with their M2 contributions. My traceability implementation and its test results are included now.

Keep requirement changes in change_register.json with exact old/new values, approval evidence and affected IDs. Regenerate the HTML and update the corresponding PED in the same reviewed change. Governance.md records the branch and PR.
