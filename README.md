# CivicConnect — M2 Engineering Baseline

CivicConnect is a citizen service-request platform for submitting requests, managing their lifecycle and providing accountable feedback. Milestone 2 connects the preserved M1 requirements to architecture, data, design and technology decisions, with an executable lifecycle service and automated traceability checks.

The [project pack](CivicConnect_Team_PED_Pack.zip) contains the application slice, schema, runnable demonstration, tests and engineering evidence. It includes PED v2.0.2, with the approved v2.0 source preserved in `baselines/`. The [repository PED](CivicConnect_PED_v2.0.docx) is also available directly. This README explains how to understand, run and continue the implementation.

## Get the project files

1. Open [CivicConnect_Team_PED_Pack.zip](CivicConnect_Team_PED_Pack.zip) and choose **Download raw file**.
2. Extract the ZIP into a local folder.
3. Open a terminal in the extracted folder containing `traceability.py`, `product/` and `tests/`. Run the commands below from that folder.

Unless linked to a repository file, the paths below refer to files inside the extracted pack.

## Current implementation

The working service supports:

- Authorised staff transitions through the defined request lifecycle.
- Acceptance with an eligible assignee and due time.
- Required explanations for rejection and resolution.
- Atomic persistence of request status and lifecycle history.
- Rejection of stale updates using an expected version.
- Requester access to their own committed status and history.
- Validation of RTM records, controlled baseline changes and recorded evidence hashes.

The RTM (`RTM.html`) retains the exact requirement statuses:

| Status | Requirements |
|---|---|
| In Development | FR-03, FR-05, FR-08, FR-12, FR-13, NFR-02 and NFR-06 |
| Not Yet Implemented | FR-01, FR-02, FR-04, FR-06, FR-07, FR-09, FR-10, FR-11, NFR-01, NFR-03, NFR-04, NFR-05 and NFR-07 |

Initial implementation and verification evidence is available for the lifecycle path. Requirement approval, implementation status and acceptance are recorded separately.

## Prerequisites and runtime

- Python 3.11 or later, with the standard `sqlite3` module. Python 3.12.x is the selected development runtime.
- A terminal opened in the extracted project folder containing `traceability.py`.
- A browser to view the generated RTM.

| Component | Recorded verification environment |
|---|---|
| Python | 3.12.14 |
| SQLite | 3.53.1, through Python's `sqlite3` module |
| Test framework | Python standard-library `unittest` |
| Third-party packages | None required for this implementation |

No package installation, database server, credentials or network connection is needed. A Python virtual environment is optional.

Check the local runtime:

```powershell
python --version
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

## Quick start

Run the lifecycle demonstration:

```powershell
python product/demo.py
```

The demo creates a temporary SQLite database, applies the schema and inserts synthetic accounts and a Submitted request. An authorised staff account accepts the request with an assignee and due time. The service commits the status and history together, then a separate connection reads the owner's saved status and explanation.

The JSON output shows:

- Request reference `CC-DEMO-001`.
- Status `Accepted` and version `1`.
- A matching committed history event and explanation.
- The local post-commit read duration.

Temporary data is removed when the demo finishes. The recorded read duration describes this local run; deployed response-time targets use their own acceptance scenarios.

Run the complete test suite:

```powershell
python -m unittest discover -s tests -v
```

Run the traceability checks and generate the browser view:

```powershell
python traceability.py validate
python traceability.py diff
python traceability.py verify-manifest
python traceability.py render
```

Open `RTM.html` from the extracted folder in a browser. Search **enforce controlled status transitions** to isolate FR-13 and view its engineering links, implementation, verification and status.

## Project structure

The extracted pack includes:

```text
product/
  lifecycle.py              Coordinator, lifecycle policy and SQLite store
  schema.sql                Accounts, requests, events and integrity constraints
  demo.py                   Executable lifecycle demonstration
  README.md                 Service-specific technical documentation
tests/
  test_lifecycle.py         Lifecycle, persistence and access tests
  test_traceability.py      RTM and evidence-control tests
evidence/
  verification.txt          Retained test results and runtime versions
  product_demo.json         Retained lifecycle demonstration output
baselines/                  Preserved engineering-document baseline
traceability.py             Validation, comparison, hash and HTML commands
baseline_m1.json            Preserved M1 requirement fields
rtm.json                    Current requirements and engineering evidence
RTM.html                    Generated searchable requirements view
change_register.json        Exact controlled changes and approval references
evidence_manifest.json      SHA-256 hashes for recorded evidence files
source_manifest.json        Original source-document identity and hash
ADRs.md                     Design and implementation decision records
Product_Trace.md            Requirement-to-verification explanation
product_trace.json          Machine-readable implementation trace
Governance.md               Repository development record
```

## Architecture and design

The architecture direction is a modular monolith: explicit responsibilities within one deployable application. The current implementation demonstrates the lifecycle and persistence responsibilities through an in-process service contract.

| Component | Responsibility |
|---|---|
| `RequestLifecycleCoordinator` | Exposes the transition command and delegates transaction mechanics to the store. |
| `LifecyclePolicy` | Validates permitted transitions and required lifecycle information without infrastructure dependencies. |
| `SqliteLifecycleStore` | Reloads access and request state, invokes the policy, commits status and history, and serves authorised history reads. |

The application call path is:

```text
Caller -> RequestLifecycleCoordinator -> SqliteLifecycleStore
                                              |
                                              +-> LifecyclePolicy
                                              +-> SQLite status/history transaction
```

The decision records in `ADRs.md` connect the implementation to its reasoning:

- **ADR-M2-01:** focused coordination makes mandatory lifecycle work explicit. New mandatory steps require deliberate orchestration changes.
- **ADR-M2-02:** status and history share one transaction, with expected-version checks and explicit conflict handling.
- **ADR-M2-03:** requester feedback comes from committed history through an in-process interface.
- **ADR-M2-04:** versioned requirements, exact change records and repeatable traceability checks support controlled development.
- **ADR-M1-02:** Python and SQLite provide the executable lifecycle implementation and real persistence evidence.

## Data model and schema setup

| Entity | Stored information and relationships |
|---|---|
| `accounts` | Identity, role, department and active state; referenced by request owners, assignees and event actors. |
| `requests` | Reference, citizen owner, department, status, submission time, assignee, due time and version. |
| `lifecycle_events` | Request reference, previous/new status, actor, event time, explanation and version. |

One account can own many requests, and one request can have many lifecycle events. Foreign keys, required fields, status checks and a unique `(reference, version)` event constraint protect structural integrity. An index supports request-history retrieval.

`SqliteLifecycleStore.initialise()` applies `product/schema.sql`. The initial schema uses `CREATE TABLE IF NOT EXISTS`; there is no versioned schema-upgrade mechanism yet. The demo and tests initialise their own databases automatically.

Writes use `BEGIN IMMEDIATE` to serialise SQLite writers. An expected-version check also rejects stale commands. Status and history either commit together or roll back together. History reads use a consistent read transaction.

The permitted lifecycle is:

```text
Submitted -> Accepted -> In Progress -> Resolved -> Closed
          -> Rejected
```

Acceptance requires an active staff assignee in the request's department and a due time after submission. Rejection and resolution require an explanation. Closed and Rejected are terminal states in this implementation.

## Service interfaces

Transition command on `RequestLifecycleCoordinator`:

```python
transition(
    actor_id,
    reference,
    target,
    expected_version,
    explanation="",
    assignee=None,
    due_at=None,
)
```

A successful command returns `reference`, `status`, `version` and `explanation` after commit.

History query on `SqliteLifecycleStore`:

```python
history(actor_id, reference)
```

The query returns the active owning citizen's current request status, version and ordered lifecycle events.

| Failure | Behaviour |
|---|---|
| `Forbidden` | Reject an inactive, unauthorised or inaccessible actor/request combination. |
| `InvalidTransition` | Reject an invalid state change, required field, assignee or timestamp. |
| `Conflict` | Reject a stale version; reload the current state and revalidate before retrying. |
| SQLite persistence error | Roll back the write transaction and propagate the error. |

The caller supplies authenticated identity. The service reloads current role, active state and department for access checks. The demo supplies synthetic identities; password authentication belongs to the future application integration.

## Automated verification

The suite contains **35 tests: 20 lifecycle/persistence/access tests and 15 traceability tests**. The retained results are in `evidence/verification.txt`.

Lifecycle tests cover valid and invalid transitions, required assignment information, rejection and resolution explanations, department and ownership access, deactivation, structural constraints, rollback, stale versions and competing updates.

Traceability tests cover requirement coverage, duplicate IDs, required fields, controlled statuses, evidence paths, exact approved changes, baseline differences, HTML escaping and evidence-hash changes.

## Traceability and baseline control

The M1 baseline preserves requirement IDs, wording, source, priority and acceptance criteria. `rtm.json` connects those requirements to ASRs, architecture, data, design, technology, implementation and verification evidence.

| Command | Purpose |
|---|---|
| `validate` | Check all 20 requirements, required fields, statuses, local evidence paths and matching approved change records. |
| `diff` | Report exact differences from preserved M1 fields. An empty list means those fields are unchanged. |
| `verify-manifest` | Compare evidence files against the hashes in `evidence_manifest.json`. |
| `render` | Generate the searchable `RTM.html` view from `rtm.json`. |

The HTML view supports engineering traceability. Its evidence fields identify local artefact paths; open those files separately to inspect their contents.

`Product_Trace.md` follows the complete FR-13 path, supported by FR-05 and FR-08:

```text
Requirement -> ASR / constraint -> Architecture responsibility
-> Data decision -> Design / interface -> Technology / ADR
-> Application artefact -> Initial verification
```

For requirement changes, record the affected IDs and exact old/new values in `change_register.json`, with the corresponding approval reference. Update related decisions, RTM entries and the PED together. Regenerate the HTML and review evidence-manifest changes when recorded artefacts change. Preserve earlier baselines and the reasons for significant decisions.

The repository development record in `Governance.md` links the engineering work to its issue, branch, commits and pull request.

## Configuration and next development steps

The current demo and tests need no environment variables, secrets, external services or HTTP endpoints. The store accepts a database path from its caller, and the demo uses a temporary local file.

Future application integration will provide browser authentication and the citizen/staff interface around the existing service contract. Deployment work will establish environment configuration, hosting, TLS and durable storage. Keep credentials and operational database files outside version control.

Further engineering evidence includes representative load testing, capacity assessment and backup/restore exercises. These results will inform any move to PostgreSQL or another server database, together with the related ADR, schema and RTM updates.
