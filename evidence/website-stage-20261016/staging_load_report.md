# CivicConnect local website staging and load test

**Result: FAIL**  
Run completed: 2026-10-16T08:45:22.409277+00:00  
Source: `feat/member-4/m3` at `4a8646bc7ea61e4d5bb05f35413bf849e83dabfe` (the tested commit is the PR #18 parent included in main merge `8d495833d58e5d6c24efaefd3e11752901b63616`).  
Runtime: Python 3.12.14; local loopback HTTP; isolated SQLite database.

## Staging checks

| Check | Result | Detail |
|---|---|---|
| login page over HTTP | PASS | HTTP 200; HTML bytes=1540 |
| stylesheet served over HTTP | PASS | HTTP 200; bytes=9407 |
| 50 distinct synthetic accounts authenticate over HTTP | PASS | authenticated=50 |
| authenticated request list renders seeded records | PASS | HTTP 200; HTML bytes=56204; records for account=200 |
| owner can open request detail | PASS | HTTP 200; HTML bytes=1798 |
| another citizen is denied request detail | PASS | HTTP 403; expected HTTP 403 |
| state-changing request without CSRF is rejected | PASS | HTTP 400; expected HTTP 400 |
| citizen submits and reopens a request through the website | PASS | form=HTTP 200; submit=HTTP 303; follow-up=HTTP 200; reference=CC-20261016-316C9C96 |
| website remains responsive after load | PASS | HTTP 200 |

## Load profile and results

- Warm-up: 56.032 seconds actual at 50 virtual users (600 requests; 88 failures).
- Measured: 50 authenticated virtual users, one owned-request detail lookup every 5 seconds for 10 minutes. All 50 users were synchronized at the start of each 5-second interval.
- Dataset: 10,000 synthetic requests across 50 synthetic citizen accounts; 200 requests per account.
- Completed samples: 6,000 / 6,000; successful: 5,353; failed: 647 (10.78333%).
- Throughput: 10.058 requests/second.
- Latency: median 533.630 ms; p95 1051.639 ms; p99 1547.513 ms; max 2073.814 ms.
- Acceptance criteria from the project NFR: p95 at or below 3,000 ms, failure rate below 1%, and 6,000 measured samples.

## Scope and limitations

This was a real HTTP run against the CivicConnect WSGI website using the same single-process server configuration as `product/serve.py`. Each virtual user authenticated over HTTP and requested its own request-detail page. Staging checks also exercised CSS delivery, request listing, cross-citizen denial, CSRF rejection, and citizen submission/detail flow.

The run used one local Windows machine and loopback HTTP. It did not exercise TLS, an external network, a production host, a reverse proxy, multiple server instances, or real users. The 647 failed samples were connection resets during synchronized bursts. Because this checkout uses a single-threaded server, the synchronized arrivals may have exceeded its pending-connection queue. This needs investigation; the failure rate means the 50-user load gate did not pass. These results do not establish production capacity or public availability.

The complete timestamped sample log is in `load_samples.csv`; the machine-readable result is in `staging_load_report.json`.


