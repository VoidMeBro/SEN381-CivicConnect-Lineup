"""NFR-03 status-lookup load test against the DEPLOYED staging release.

Operation under test: SqliteLifecycleStore.history(actor, reference), the only
requester status-lookup path implemented in the release candidate (FR-03/FR-08).
Workload: N virtual users (threads), each with its own store instance, one
authorised lookup per think-time interval against a database of S stored requests.
Warm-up samples are discarded. Load generator and system under test share one host
and one process, which is a recorded limitation.
"""
import argparse, json, os, platform, random, sqlite3, statistics, sys, threading, time
from datetime import datetime, timezone
from pathlib import Path

def seed(store, requests_total, citizens=1000, seed_value=381):
    rnd = random.Random(seed_value)
    c = store.connect()
    try:
        with c:
            c.executemany("INSERT INTO accounts VALUES(?,?,?,?)",
                          [(f"cit-{i}", "Citizen", "", 1) for i in range(citizens)] +
                          [(f"stf-{d}-{i}", "Staff", d, 1) for d in ("Water", "Roads", "Waste", "Power") for i in range(5)])
            chain = ["Accepted", "In Progress", "Resolved", "Closed"]
            reqs, events, owners = [], [], []
            for n in range(requests_total):
                ref, owner = f"CC-LT-{n:06d}", f"cit-{rnd.randrange(citizens)}"
                dept = rnd.choice(("Water", "Roads", "Waste", "Power"))
                steps = rnd.choice([0, 0, 1, 2, 3, 4])
                staff = f"stf-{dept}-0"
                reqs.append((ref, owner, dept, "Submitted" if steps == 0 else chain[steps - 1],
                             "2026-09-01T08:00:00+00:00", staff if steps else None,
                             "2026-09-10T08:00:00+00:00" if steps else None, steps))
                prev = "Submitted"
                for k in range(steps):
                    events.append((ref, prev, chain[k], staff, f"2026-09-0{k+2}T08:00:00+00:00", f"Update {k+1} for {ref}", k + 1))
                    prev = chain[k]
                owners.append((owner, ref))
            c.executemany("INSERT INTO requests(reference,citizen_id,department,status,submitted_at,assignee,due_at,version) VALUES(?,?,?,?,?,?,?,?)", reqs)
            c.executemany("INSERT INTO lifecycle_events(reference,from_status,to_status,actor,occurred_at,explanation,version) VALUES(?,?,?,?,?,?,?)", events)
        return owners, len(events)
    finally:
        c.close()

def percentile(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--env-root", required=True); p.add_argument("--out", required=True)
    p.add_argument("--users", type=int, default=50); p.add_argument("--requests", type=int, default=10000)
    p.add_argument("--think", type=float, default=5.0); p.add_argument("--warmup", type=float, default=60)
    p.add_argument("--duration", type=float, default=600); p.add_argument("--label", default="NFR-03 profile")
    a = p.parse_args()
    if os.environ.get("CIVICCONNECT_ENV") != "staging":
        sys.exit("Set CIVICCONNECT_ENV=staging")
    root = Path(a.env_root).resolve(); current = (root / "current").resolve()
    sys.path.insert(0, str(current / "product"))
    from lifecycle import SqliteLifecycleStore
    release = json.loads((current / "release.json").read_text(encoding="utf-8"))
    db = root / "data" / f"load-{a.requests}.sqlite3"
    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(str(db) + suffix).unlink(missing_ok=True)
    base = SqliteLifecycleStore(db); base.initialise()
    t0 = time.perf_counter(); owners, event_count = seed(base, a.requests)
    seed_seconds = round(time.perf_counter() - t0, 2)
    by_owner = {}
    for owner, ref in owners:
        by_owner.setdefault(owner, []).append(ref)
    users = random.Random(7).sample(sorted(by_owner), a.users)

    samples, failures, lock = [], [], threading.Lock()
    start = time.perf_counter(); warm_end = start + a.warmup; end = warm_end + a.duration

    def vu(index, user):
        rnd = random.Random(index); store = SqliteLifecycleStore(db)
        time.sleep(rnd.uniform(0, a.think))     # stagger start
        while time.perf_counter() < end:
            ref = rnd.choice(by_owner[user]); began = time.perf_counter()
            try:
                result = store.history(user, ref)
                assert result["reference"] == ref
                elapsed = time.perf_counter() - began; ok = True
            except Exception as exc:
                elapsed = time.perf_counter() - began; ok = False
                with lock: failures.append(f"{type(exc).__name__}: {exc}")
            if began >= warm_end:
                with lock: samples.append((elapsed, ok))
            time.sleep(max(0, a.think - elapsed) if a.think else 0)

    threads = [threading.Thread(target=vu, args=(i, u)) for i, u in enumerate(users)]
    for t in threads: t.start()
    for t in threads: t.join()
    lat = [s for s, ok in samples if ok]
    fail_rate = (len(samples) - len(lat)) / len(samples) if samples else 1.0
    p95 = percentile(lat, 0.95) if lat else None
    within3 = sum(1 for x in lat if x <= 3.0) / len(samples) if samples else 0
    report = {
        "label": a.label, "release_id": release["release_id"], "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "operation": "SqliteLifecycleStore.history(actor_id, reference) - authorised requester status lookup",
        "workload": {"virtual_users": a.users, "stored_requests": a.requests, "stored_events": event_count, "think_time_s": a.think,
                     "warmup_s": a.warmup, "measured_s": a.duration, "seed_s": seed_seconds},
        "environment": {"platform": platform.platform(), "cpu_count": os.cpu_count(), "python": platform.python_version(),
                        "sqlite": sqlite3.sqlite_version, "topology": "load generator threads and service in one process on one host; local file database; no network, no HTTP layer, no authentication layer"},
        "results": {"samples": len(samples), "failures": len(samples) - len(lat), "failure_rate": round(fail_rate, 5),
                    "throughput_per_s": round(len(samples) / a.duration, 2),
                    "p50_s": round(statistics.median(lat), 6) if lat else None, "p95_s": round(p95, 6) if p95 is not None else None,
                    "p99_s": round(percentile(lat, 0.99), 6) if lat else None, "max_s": round(max(lat), 6) if lat else None,
                    "share_within_3s": round(within3, 5)},
        "nfr03_targets": {"p95_within_3s": bool(p95 is not None and p95 <= 3.0 and within3 >= 0.95), "failure_rate_below_1pct": fail_rate < 0.01},
        "failure_examples": failures[:3],
    }
    Path(a.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["results"], indent=2)); print(json.dumps(report["nfr03_targets"]))

if __name__ == "__main__":
    main()
