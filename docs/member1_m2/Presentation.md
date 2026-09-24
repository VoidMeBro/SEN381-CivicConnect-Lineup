# My Member 1 M2 presentation

## Five minute route

0:00–0:45: Our PED continues the approved M1 baseline. I preserved the original requirements and sign-off and evolved the same document to v2.0.1. Open document control and version history.

0:45–1:30: I reviewed scope, acceptance, constraints, assumptions and all seven forward considerations. Show CR-M2-05: control and tooling changed; requirement wording did not. Explain that future baseline edits need exact approved old/new values.

1:30–2:30: Open RTM.html, search FR-13, and show source, criteria, lifecycle responsibility, atomic status/history decision and ADR-M2-01/02. Search FR-08 for approved in-app feedback and ADR-M2-03. Explain the final incoming implementation links from the other members.

2:30–3:45: Search NFR-06. Run validate, diff and verify-manifest, then show evidence/verification.txt and the tests. Trace source -> ASR-T01 -> traceability module -> JSON records -> command interface -> ADR-M1-01/ADR-M2-04 -> code -> actual test output.

3:45–4:30: Show the product acceptance path in Section 33: staff accepts Submitted work with assignee and due time; the committed history becomes visible to its requester. Explain the coordinator, transaction and ownership boundaries. Member_Handoff.md lists the final incoming artefacts.

4:30–5:00: Open the branch/PR in Governance.md and show the ten-task checklist. Summarise what my code verifies and what the application tests must prove.

## Defence answers

- Why Mediator? Mandatory authorisation, validation and history need an explicit coordinator. Observer adds registration and ordering risks for mandatory steps.
- Why atomic history? A successful status change must not lose its accountability record or expose feedback for a failed transaction.
- Why in-process calls? Our internal workflow needs clear responsibilities, not an invented network boundary.
- Why versioned JSON? It enables exact baseline comparison and repeatable checks for our 20 requirements without operating another service.
- Why separate approval and implementation? We can approve what must be built before the corresponding feature and tests exist.
- Does a hash prove correctness? It identifies the checked bytes. Tests and reviews establish what those bytes do.
- What happens when requirements change? Preserve old values, approve a matching CR, update PED/RTM/ADR/tests together, and review the exact commit.
