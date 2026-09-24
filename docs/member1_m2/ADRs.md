# Approved Member 1 integration decisions

I approve these decisions for the M2 traceability baseline. They apply M1 requirements and Assignment 2 research to CivicConnect; the other members supply their detailed M2 implementation artefacts.

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