# The Member 1 M2 presentation

## Five minute demonstration

0:00–0:45: Open PED document control and version history. Explain the M1-to-v2.0.2 continuity, approved four-member allocation and unchanged 20 requirement wordings.

0:45–1:30: Open change_register.json and show CR-M2-06. Explain why adding initial code changes evidence rather than the requirement. Run `python traceability.py diff` to show no requirement differences.

1:30–2:15: Open RTM.html and search FR-13. Trace its source, criteria, ASR-L01/L02/L03, coordinator/policy, transaction schema, ADR-M1-02 and implementation paths. Show ADR-M2-01/02/03 and the A2 sections supporting each decision.

2:15–3:30: Run `python product/demo.py`. Show Accepted status, actor/time/explanation and the owning requester's separate-connection history read. Open tests/test_lifecycle.py at the rollback and competing-update tests; show actual evidence/verification.txt. Explain that this is initial service evidence, not a completed web application.

3:30–4:15: Search NFR-06. Run `python traceability.py validate` and `python traceability.py verify-manifest`. Explain exact approved-change matching, safe evidence paths and hashes. A hash identifies bytes; tests establish behaviour.

4:15–5:00: Open Governance.md and the actual issue/PR. Show Member1_Completion_Checklist.md. Explain that peer approvals and the live presentation are performed by the responsible people, while the authored work and executed evidence are available now.

## Defence points

- Mandatory history belongs in the same transaction as the status change; an optional observer cannot silently omit it.
- The store loads current state inside the transaction before calling the independent policy, avoiding stale cached validation.
- Expected versions reject stale commands; two simultaneous commands have one winner. A conflict requires a fresh read, not a blind retry.
- Staff department and active account state are rechecked on every operation; history is restricted to the active owner.
- Python/SQLite were chosen for a reproducible initial reference slice without imposing a whole-application stack on Member 4.
- Full browser authentication, deployed 5/60-second visibility and load targets are not proven by a local service test. The RTM therefore keeps affected requirements In Development.
- M1/A2 decisions, actual code and tests are reflected in the same PED/RTM/ADR revision. Later member submissions can extend this evidence through controlled changes.
