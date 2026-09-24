# CivicConnect Member 1 M2 pack

Open `CivicConnect_PED_v2.0_Member1.docx` for the continuing PED and `RTM.html` for a searchable view of all 20 requirements. The supplied M1 document is preserved unchanged as `M1_original_v0.11.docx` and identified by SHA-256 in `source_manifest.json`.

The user confirmed on 24 September 2026 that all four members signed off v0.11. This pack records that confirmation without inventing the original review date or individual signatures. Four members are the confirmed allocation. The M2 candidate itself still requires human review.

## Contents

- PED: existing M1 sections plus M2 control, review, changes, risks, full RTM, decision and trace records.
- `rtm.json`: editable RTM, with every required M2 field group and separate approval/acceptance states.
- `baseline_m1.json`: preserved source requirement wording, sources, priorities and criteria.
- `traceability.py`: project-specific engineering control implementing part of NFR-06.
- `tests/test_traceability.py`: positive and negative integrity tests.
- `evidence/verification.txt`: actual automated run, not a human check-off log.
- `Human_Review.md`: user-attested M1 completion and pending M2 review.
- `Sample_Checkoff.md`: explicitly fictional examples, excluded from approval evidence.
- `Presentation.md`: live demonstration route and engineering defence.
- `PR_Draft.md`: local task and proposed review text, not a claim that a remote PR exists.

## Run

Use Python 3.11 or later. No third-party packages, database, environment variables, network or credentials are needed for the traceability tool.

From this directory:

```powershell
python traceability.py validate
python -m unittest discover -s tests -v
python traceability.py render
```

`validate` exits 0 if structural checks pass and 1 on invalid input. `render` regenerates the standalone HTML from JSON; open it in a browser. Search `FR-13` for the product-path target or `NFR-06` for the implemented tooling evidence.

## Responsibilities and limitations

The tool checks exact M1 coverage, required fields, controlled statuses, change references, local evidence existence and containment. It escapes text for HTML rendering. It does not establish that evidence content is correct, authenticate reviewers or prove product acceptance. A change reference must be reviewed by a human; its mere presence does not prove approval.

All proposed architecture, data and interface allocations need the relevant owner's decision. Application stack selection remains Member 4's responsibility; the Python tooling choice does not commit the application to Python. The existing local repository inspected for this task contained M1 documentation, not product code. No later remote work was assumed absent.

The complete tooling trace is NFR-06 -> ASR-T01 -> local control module -> versioned JSON -> validation interface -> ADR-M1-01 -> code -> tests. M2's actual citizen-service product trace remains an integration dependency: obtain Member 2 architecture/design evidence, Member 3 schema/interface/transaction tests and Member 4 stack/bootstrap evidence, then update the FR-13/05/08 chain. Do not present that planned path as executed.

## Controlled updates

Edit JSON, regenerate HTML, update the matching PED records, rerun tests and review all changed evidence. Preserve M1 source and prior approved revisions. Use an approved CR for material requirement changes. Obtain genuine M2 human review and two independent non-author PR approvals before baseline or merge. The local development task is M1-M2-TRACE.
