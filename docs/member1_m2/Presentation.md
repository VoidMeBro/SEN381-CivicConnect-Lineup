# Member 1 presentation and defence

1. Open the PED control table and Section 26. Explain that v2.0 evolves the same PED and preserves the supplied v0.11. State that the user confirms team sign-off of v0.11; do not invent a v1.0 version.
2. Open Sections 27 and 28. Show one concrete change issue: the documented confirmation of four members and v0.11 sign-off. Explain why proposed acceptance targets remain unchanged.
3. Open RTM.html and search FR-13. Show source, exact criteria, proposed responsibility and explicitly absent implementation evidence. Contrast with NFR-06, which has real tooling evidence but still lacks acceptance.
4. Run `python traceability.py validate` then `python -m unittest discover -s tests -v`. Open the saved verification log. Show that a structural check is not human sign-off.
5. Trace NFR-06 through ADR-M1-01 and the code/tests. Then show the planned citizen lifecycle path in Section 33 and identify the missing Member 2/3/4 artefacts candidly.
6. Close with the precise baseline gate: actual M2 human reviews, product evidence, exact revision and two independent approvals.

## Likely defence questions

- Why JSON as well as Word? Stable machine-readable records permit repeatable integrity checks; the PED explains reasoning. Both must be updated in the same reviewed change.
- Does a file existing prove implementation? No. The tool rejects some invalid claims, but a human must inspect whether the artefact actually meets the criterion.
- Why not mark all requirements Approved? M1 is team-approved per user confirmation; approval is separate from implementation, and new M2 decisions still require review.
- Why no Assignment 2 RTM column? Research informs ADRs; the RTM traces engineered requirements.
- Is the end-to-end application path complete? No. A tooling trace exists; product-path artefacts from Members 2 to 4 are still required.
- What if a target changes? Preserve old wording, assess impact, obtain an approved CR, revise RTM/PED/tests together and retain the earlier baseline.
