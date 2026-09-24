# Executed CivicConnect lifecycle trace

I completed an executable initial product path for FR-13, FR-05 and FR-08. This is Member 1 implementation evidence applying our approved decisions; it is not attributed to the other members.

## Run

```powershell
python product/demo.py
python -m unittest discover -s tests -v
```

The demo creates a temporary SQLite database containing synthetic accounts and one Submitted request. Active Water-department staff accept it with a valid assignee and due time. The service commits the status and accountability event together. A separate connection reads the owner's Accepted status and saved explanation. Temporary data is removed when the run ends.

## Complete trace

| Stage | Decision and evidence | Artefact |
|---|---|---|
| Requirement | FR-13 controls transitions; FR-05 saves remarks, actor and time; FR-08 exposes meaningful requester feedback. | baseline_m1.json |
| ASR and constraint | ASR-L01 mandatory status/history atomicity, ASR-L02 ownership and staff-department access, ASR-L03 stale-update rejection. NFR-02 and the M1 no-budget constraint apply. | Product_Trace.md |
| Architecture responsibility | RequestLifecycleCoordinator receives an in-process command, LifecyclePolicy checks the transition, and SqliteLifecycleStore owns atomic persistence and authorised history reads. | product/lifecycle.py |
| Data decision | Accounts, requests and lifecycle_events; unique reference/version, foreign keys, status constraints, one write transaction and a consistent read snapshot. | product/schema.sql |
| Design and interface | transition(actor_id, reference, target, expected_version, explanation, assignee, due_at); history(actor_id, reference). Explicit Forbidden, Conflict and InvalidTransition failures. | product/lifecycle.py |
| Technology and ADR | ADR-M1-02 uses Python 3.12.14 and bundled SQLite 3.53.1 for this executable reference slice. ADR-M2-01/02/03 supply the approved domain decisions. | ADRs.md |
| Application artefact | The real service commits Submitted to Accepted, then a separate connection reads the same status and explanation for the owning citizen. | product/demo.py |
| Initial verification | 20 lifecycle/persistence/access tests plus 15 traceability tests pass. Demo output records the saved event and an actual local post-commit read time. | evidence/verification.txt |

## Initial verification scope

The tests exercise valid acceptance, complete lifecycle, mandatory assignee/due time, rejection/resolution explanations, invalid and terminal transitions, inactive/wrong-department access, citizen ownership, rollback when history insertion fails, stale commands and simultaneous competing writes. Structural foreign-key/status constraints are tested directly.

The caller supplies an authenticated actor ID; account role, department and active state are reloaded on every operation. A web login, browser UI, deployment and performance/load targets are outside this initial service. The actual local post-commit read time is recorded in evidence/product_demo.json and is not a claim that deployed FR-05/FR-08 timing targets have passed.

## Architecture and data responsibilities

```text
Authenticated caller / offline demo
                 |
                 v
RequestLifecycleCoordinator -> SqliteLifecycleStore -> LifecyclePolicy
                                        |
                                        v
                        one status + history transaction
                        accounts / requests / lifecycle_events
                                        |
                                        v
                    authorised requester history read snapshot
```

The policy is infrastructure-independent. The store loads current state and invokes the policy inside the transaction to avoid validating a stale cached record. The coordinator exposes the workflow contract and delegates transaction mechanics. No HTTP endpoint or network boundary is invented for these in-process calls.

## Member evidence reconciliation

Our A2 Task 1A coordinator responsibilities, Task 1B in-app feedback, Task 2 atomic/versioned persistence and Task 3 internal interface are reflected in the actual source, schema, tests, ADRs and RTM. A2 Task 4 informs our branch/review workflow and repeatable commands. The standalone reference slice gives Member 1 an executed trace now. Members 2–4 retain ownership of their wider M2 submissions; when received, their final application paths replace or extend this reference evidence through controlled updates.
