# Final release decision

**Decision:** NO-GO for production release.
**Application and evidence baseline:** `c8fcc9887d58bc07e7b592e292dbe05222d97190`
**Date:** 17 October 2026
**Team review:** Approved collectively by the project team after checking and verifying the final evidence and decision.

## Basis

The integrated local website profile used 50 authenticated virtual users, 10,000 synthetic requests and 6,000 measured lookups over ten minutes. The p95 latency was 1,051.639 ms against a 3,000 ms limit. The run recorded 647 failed requests out of 6,000 (10.78333%), exceeding the M1 limit of less than 1%. Staging checks passed 9 of 9, but this does not offset the failed reliability gate. The 20-weekday availability criterion also has no supporting probe record. NFR-01 remains an unmet Must Have: the team deferred the five-person usability study while prioritising the load-reliability issue, and insufficient time remained before M4 closure. The team reviewed and verified this reason and status.

The profile ran over loopback HTTP on one Windows host against the single-process local WSGI server. Connection resets occurred during synchronized bursts. A pending-connection queue limit is a hypothesis in the test report, not a confirmed cause. No production capacity or public availability claim is made.

## Allowed demonstration boundary

A local academic demonstration may proceed with synthetic data and the local server. This is not a production or simulated-production release. No real citizen information should be used. The demonstration must disclose the failed load result and the absence of availability evidence.

## Conditions before production reconsideration

1. Identify the root cause of the connection resets and document the corrective decision.
2. Resolve the reliability failure without weakening the acceptance threshold.
3. Repeat the same 50-user, ten-minute profile with at least 6,000 samples.
4. Demonstrate p95 latency at or below 3,000 ms and failure rate below 1%.
5. Record the exact assessed commit and revalidate critical journeys on that baseline.
6. Provide deployment, security, data-integrity, backup and availability evidence appropriate to the target environment.

The original M3 local demonstration approval remains a historical academic-scope decision. This M4 no-go decision governs production readiness.
