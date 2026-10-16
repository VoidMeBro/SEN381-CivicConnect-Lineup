"""Small local request-history lookup load check; not a production capacity test."""

from concurrent.futures import ThreadPoolExecutor
import math
import json
from pathlib import Path
import statistics
import tempfile
import time

from lifecycle import SqliteLifecycleStore, seed_demo


def main():
    temp_root = Path(__file__).resolve().parents[1] / ".test-tmp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="civicconnect-perf-", dir=temp_root) as directory:
        store = SqliteLifecycleStore(Path(directory) / "load.sqlite3")
        store.initialise()
        seed_demo(store, "LocalPerformance-381!")
        connection = store.connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.executemany(
                    "INSERT INTO requests(reference,citizen_id,department,status,submitted_at,title,description,location,category_id,category_label) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?)",
                    ((f"CC-PERF-{i:05d}", "citizen-a", "Water", "Submitted", "2026-10-01T08:00:00+00:00", "Load request", "Synthetic performance record.", "Test area", "water", "Water") for i in range(10_000)),
                )
        finally:
            connection.close()
        references = [f"CC-PERF-{i:05d}" for i in range(50)]
        def lookup(reference):
            started = time.perf_counter()
            result = store.history("citizen-a", reference)
            return time.perf_counter() - started, result["status"] == "Submitted"
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(lookup, references))
        elapsed = time.perf_counter() - started
        latencies = sorted(seconds for seconds, ok in results if ok)
        failures = len(results) - len(latencies)
        p95 = latencies[max(0, math.ceil(len(latencies) * .95) - 1)] if latencies else None
        print(json.dumps({
            "operation": "authenticated request-history lookup",
            "records": 10001,
            "concurrent_users": 50,
            "lookups_per_user": 1,
            "failures": failures,
            "elapsed_seconds": round(elapsed, 4),
            "p95_seconds": round(p95, 4) if p95 is not None else None,
            "target_seconds": 3.0,
            "target_met_for_this_scenario": failures == 0 and p95 is not None and p95 < 3.0,
            "limitations": "One local process and machine; one lookup per user; no 10-minute soak, remote network, production workload, or availability claim.",
        }, indent=2))


if __name__ == "__main__":
    main()
