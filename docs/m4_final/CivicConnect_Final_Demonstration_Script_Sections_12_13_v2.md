# CivicConnect final demonstration video script

**Basis:** SEN381 FINAL, Sections 12 and 13  
**Format:** Four speakers in consecutive blocks. Speaker 1 covers slides 1–3, Speaker 2 covers slides 4–6, Speaker 3 covers slides 7–9, and Speaker 4 covers slides 10–12.  
**Opening footage:** One continuous product demonstration at the start, using synthetic data on the local server. The remainder of the recording follows the PowerPoint. Text in brackets is a recording cue and is not spoken.

## Opening product demonstration

**Speaker 1**

[Start one continuous screen recording. Show a citizen signing in with a synthetic account, submitting a request and seeing its reference and status. Continue as staff to open the request and record an allowed update. Finish on the management summary. Do not switch to another demonstration later in the video.]

CivicConnect brings the main service-request workflow into one local application. We will show one complete example using synthetic records. A citizen submits a request and receives a reference. Staff can review the request and record an authorised update. The management view summarises service activity. This recording shows the application running locally for the academic project.

## Speaker 1 — Slides 1–3: Final product

### Slide 1 — CivicConnect final project

[Return to the title slide. Keep the full assessed application baseline visible on screen; do not read the commit string aloud.]

This video documents our completed CivicConnect project against the final application and evidence baseline shown here. It follows the final demonstration structure in Section 12 of the SEN381 Final document. The video covers the product, the signed-off M1 scope and final status, M3 integration and closure, the final evidence, and the project outcome. Our assessed product is the local server-rendered application using SQLite and synthetic data.

### Slide 2 — Combined critical journeys

[Use the three journey labels on the slide to refer back to the opening product footage.]

The opening footage covered the critical journeys together. Citizens register or sign in, submit a validated service request, and review its reference and history. Staff work within their authorised department queues and record permitted lifecycle changes. Management can review request totals and work status. These are the product capabilities assessed against the final M1 requirements. The opening capture used synthetic data and the local application.

### Slide 3 — Product version and operating boundary

[Point to the application baseline and the evidence boundary.]

Our final evidence baseline is recorded in the submission artifacts and shown on this slide. The application runs locally on our own server, with a server-rendered Python interface and a local SQLite database. The earlier M3 CI result belongs to its recorded application commit and run, which are identified separately on screen. The M4 website checks passed 9 of 9 functional checks. The project team checked and verified the reported results. The product is suitable for the local academic demonstration boundary. Section 13 also asks us to state the deployment decision, which we will explain after the final load evidence.

## Speaker 2 — Slides 4–6: M1 scope and final acceptance

### Slide 4 — M1 commitments and final delivery

[Move through the four status groups. The detailed requirement-by-requirement record is in the final RTM.]

We compared the signed-off M1 baseline with the final implementation and evidence. FR-01 through FR-13 and NFR-02 are recorded as met for the assessed application paths. NFR-03, NFR-05, NFR-06 and NFR-07 are partial because some acceptance conditions were not met or were not evidenced. NFR-01 and NFR-04 are unmet. This makes the change from M1 visible: the core citizen, staff and management workflows were delivered, while several non-functional criteria remained incomplete. The final RTM records each status and its supporting evidence.

### Slide 5 — Recorded M1 scope calculation

[Point to the native editable table and the formula. Keep “requirement-row summary” visible.]

Our signed-off scope worksheet records 20 M1 requirement rows. Fourteen met rows contribute 14 points. Four partial rows contribute two points, and two unmet rows contribute zero. The result is 16 out of 20, or 80 percent. This is the requirement-row summary calculated by the worksheet. Some rows contain more than one acceptance condition, and the RTM retains those conditions and their evidence. The 80 percent figure does not change the status of the unmet Must Have criteria.

### Slide 6 — Final acceptance status

[Emphasise the two unmet requirements and the Must Have classification for NFR-01.]

NFR-01 required five first-time representative users to complete the same valid submission scenario, with at least four completing within five minutes without assistance. We prioritised the load-reliability issue, and there was not enough time to complete the study before project closure, so we deferred it. The team checked and verified this reason and the unmet status. NFR-02 met its recorded role and ownership checks. NFR-03 met its latency limit but failed its request-failure limit. NFR-04 has no 20-weekday availability probe. The remaining partial statuses are recorded in the RTM with their evidence boundaries.

## Speaker 3 — Slides 7–9: M3 closure and release decision

### Slide 7 — M3 integration and closure

[Show the integrated application evidence separately from any lifecycle-slice results.]

The integrated M3 application brought the citizen, staff and management workflows together. The recorded regression run completed with 37 tests passed, zero failures and zero errors. The configured GitHub Actions workflow also passed on the application baseline shown on screen. At M4, the integrated website checks passed 9 of 9. During closure, we confirmed that DEF-001, the PED heading, was corrected in v3.0. DEF-002 remains scoped to the preserved M2 pack, and DEF-003 remains scoped to the separate lifecycle slice. We do not classify either as an integrated website defect. DEF-004 records the integrated website resets and remains the production blocker. The separate lifecycle-slice performance result is not evidence for integrated website capacity.

### Slide 8 — Integrated website load result

[Pause on the measured result. Keep the p95 pass and request-failure fail equally clear.]

The M4 website profile used 50 authenticated virtual users, 10,000 synthetic requests and 6,000 measured requests over ten minutes. The 95th-percentile latency was 1,051.639 milliseconds, below the 3,000-millisecond limit. However, 647 of 6,000 requests failed, a rate of 10.78333 percent. The acceptance limit is below one percent, so the reliability gate failed. The report records connection resets during synchronized bursts. A pending-connection queue limit is a possible explanation, not a confirmed root cause. This was a single-host loopback HTTP run, so the result does not establish public or production capacity.

### Slide 9 — Final deployment decision

[Read the status and boundary from the slide.]

Our final production decision is NO-GO. The measured failure rate exceeded the NFR-03 limit, NFR-04 availability evidence is absent, and the NFR-01 Must Have study was deferred. A local academic demonstration with synthetic data is permitted within the recorded boundary. The earlier M3 local demonstration approval applied to the school-project scope and does not represent production approval. This is the release decision at project closure.

## Speaker 4 — Slides 10–12: Evidence and project conclusion

### Slide 10 — Final evidence and artifact closure

[Show the evidence map and the final artifact list.]

The final RTM connects the M1 requirements to their implementation status, verification evidence and outcome. The final package includes PED v4, the RTM, the scope worksheet, risk, defect, technical-debt and AI registers, and the release decision. The project team completed the collective final review and checked and verified the recorded calculations, evidence references, statuses and artifacts. The assessed application baseline is distinct from the documentation branch. Individual defence questions are assessed separately from this collective demonstration.

### Slide 11 — Decisions and project consequences

[Use the slide’s decision-to-consequence statements.]

We kept the application local and used our own server and synthetic data. Hosting and platform cost for this setup was zero. We met every project deadline. The local architecture supported the academic demonstration, while the integrated website profile exposed a reliability limit under synchronized load. We did not treat the test report’s possible queue explanation as a confirmed cause. We also consolidated AI activity into one project register. The team checked and verified each recorded activity against the retained project evidence, and the team remained responsible for the submitted decisions and content.

### Slide 12 — Project conclusion

[Close on the completed project outcome and final release boundary.]

We completed CivicConnect as a local academic service-request system with connected citizen, staff and management workflows. Our final worksheet records 80 percent requirement-row completion, and the RTM shows the status and evidence for each M1 requirement. We met every deadline, incurred zero hosting and platform cost for the local setup, and completed the collective review of the final submission. The production no-go is our final release decision, based on the failed reliability threshold and the outstanding usability and availability criteria. The project is complete within its submitted academic scope. Thank you.

## Recording notes

- Keep the complete application baseline and the separate CI baseline visible in the relevant evidence slides. Speakers should refer to the identifiers on screen instead of reading long strings.
- Keep the opening product footage as the only demonstration. Use synthetic accounts and synthetic requests.
- Use the exact wording and numbers shown in the slide deck and final project records. Do not describe the possible queue limit as a confirmed cause.
- The team recording covers the collective assessment in Section 13. Each member's individual defence remains a separate assessment.

