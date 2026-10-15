# Approved Member 1 integration decisions

These decisions for the M2 traceability baseline are approved. They apply M1 requirements and Assignment 2 research to CivicConnect; the other members supply their detailed M2 implementation artefacts.

## ADR-M2-01 Lifecycle coordination

Status: Approved

Source: FR-05 and FR-13; A2 Task 1A

Decision: Use a focused RequestLifecycleCoordinator to authorise, validate and coordinate the status/history transaction. Keep lifecycle rules in LifecyclePolicy and persistence behind its contract.

Alternatives: Observer was rejected for mandatory status/history work because registration and ordering obscure required steps. A generic mediator framework is unnecessary.

Consequences: Mandatory work is explicit and testable. The coordinator must remain focused; new required steps change orchestration.

## ADR-M2-02 Persistence integrity

Status: Approved

Source: FR-05, FR-12 and FR-13; A2 Task 2

Decision: Enforce authorisation and lifecycle rules in the application; enforce structural constraints in persistence. Commit status and history in one transaction. Use an atomic expected-version check and revalidation after a conflict.

Alternatives: Application-only validation cannot protect structural integrity from every write path. Blind retries and independent history writes were rejected.

Consequences: Failures leave neither a partial status update nor a partial history event. Conflict handling adds explicit failure paths and tests.

## ADR-M2-03 Feedback and internal interface

Status: Approved

Source: FR-03, FR-08 and NFR-02; A2 Task 1B and Task 3

Decision: Read requester-visible feedback from committed lifecycle history under ownership checks. Use an in-process application/service contract for internal calls. Introduce REST only at a real client/server or external boundary.

Alternatives: A multi-channel Strategy hierarchy and provider Adapter are unnecessary for the current in-app scope. An internal network split adds deployment and failure complexity without a current requirement.

Consequences: Feedback stays consistent with committed state. Additional delivery channels require controlled scope and interface changes.

## ADR-M2-04 Traceability and review integration

Status: Approved

Source: NFR-06; A2 Task 4

Decision: Keep short-lived branches, substantive PRs, two independent approvals and repeatable local checks. Store RTM and exact change records in versioned JSON and generate the live HTML from that data.

Alternatives: Direct writes to main and document-only evidence checks were rejected. A hosted requirements database adds unnecessary operational overhead for 20 requirements.

Consequences: Checks expose broken links and unauthorised baseline differences. Human review still assesses correctness and provides independent approvals.

## ADR-M1-02 Executable initial lifecycle reference slice

Status: Approved for Member 1 initial development and trace demonstration.

Problem: the documentation defined a complete lifecycle trace but had no executable path. Reproducible evidence is required of the approved rules without claiming other members have delivered code that has not been received.

Decision: implement the in-process lifecycle service with the already available Python standard library and SQLite, using synthetic local data. The verified environment is Python 3.12.14 and SQLite 3.53.1. This choice commits the reference slice only; it does not replace Member 4's full application technology comparison.

Alternatives: a mocks-only demo would not prove transactional persistence; introducing a web framework and hosted database would expand this Member 1 task and invent deployment commitments. The local relational store demonstrates real commit/rollback and ownership behaviour at low setup cost.

Data and concurrency: state and mandatory history share one transaction. SQLite serialises writers with BEGIN IMMEDIATE; an expected-version predicate rejects stale commands. No blind retry occurs. A Conflict requires a fresh read and revalidated command. History uses a consistent read transaction. Foreign keys, non-null/check constraints and a unique request/version event guard structural integrity.

Consequences: the initial path is executable and testable with no third-party packages or secrets. Local SQLite serialisation is not evidence of final multi-user capacity, database availability or hosted deployment. The later application may use another store behind the same behaviour contract. The actor parameter is an authenticated-context boundary; the offline demo is not a login implementation.

Trace links: FR-05, FR-08, FR-13, NFR-02; ASR-L01/L02/L03; ADR-M2-01/02/03; CR-M2-06; R-12, R-17, R-18. Evidence: Product_Trace.md, product_trace.json, product/lifecycle.py, product/schema.sql, product/demo.py, tests/test_lifecycle.py and the actual execution logs.
