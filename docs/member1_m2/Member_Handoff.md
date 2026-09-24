# Required product evidence handoff

Target: FR-13 staff acceptance of Submitted work, FR-05 saved-state visibility and FR-08 requester feedback. Preserve approved criteria. This is an integration request specification, not a message sent to team members.

| Owner | Required artefacts | Member 1 consistency check |
|---|---|---|
| Member 2 | ASR IDs, selected architecture diagram/ADR, lifecycle design ADR and component paths | Authorisation and lifecycle responsibility match FR-13; rejected alternatives and A2 Task 1A rationale recorded |
| Member 3 | Schema/migration, transaction implementation, history query contract, tests and actual output | Status/history atomicity, required assignee/due time, rejection/resolution explanations, ownership, rollback and concurrency behaviour |
| Member 4 | Runtime/store version manifest, bootstrap/run command, deployment compatibility ADR, application commit/PR | Recorded stack matches executable code; documented configuration is sufficient; no committed secrets |

For each artefact supply repository-relative path, exact commit, owner, decision ID and verification command/result. Member 1 then links the same identifiers into the PED, RTM and ADR records and reruns consistency checks.

Product acceptance scenarios: valid acceptance; missing assignee; missing/invalid due time; invalid transition; unauthorised staff; non-owner citizen history request; persistence failure rollback; two competing transitions; requester sees saved state within 5 seconds and history feedback within 60 seconds. Record observed values and test environment. These scenarios have not been executed against a supplied product application.

Ready gate: each stage has an actual artefact, the feature works under the documented command, tests verify the claimed criterion, and the RTM/ADR/PED refer to the same revision. Only then mark the product trace complete.
