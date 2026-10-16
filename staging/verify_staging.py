"""Post-deployment verification of the staging environment.

Runs against the DEPLOYED copy (<env-root>/current), never the source tree.
Covers release integrity, schema integrity, the critical journey (FR-13/05/08:
accept -> progress -> resolve -> close, then citizen reads status and history),
negative/unauthorised cases (NFR-02), restart persistence and a backup/restore
check. Writes JSON evidence and exits non-zero on any failure.
"""
import argparse, hashlib, json, os, sqlite3, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if os.environ.get("CIVICCONNECT_ENV") != "staging":
        sys.exit("Set CIVICCONNECT_ENV=staging")
    root = Path(args.env_root).resolve()
    current = (root / "current").resolve()
    sys.path.insert(0, str(current / "product"))
    import lifecycle
    from lifecycle import SqliteLifecycleStore, RequestLifecycleCoordinator, Forbidden, Conflict, InvalidTransition
    release = json.loads((current / "release.json").read_text(encoding="utf-8"))
    db = root / "data" / "civicconnect-staging.sqlite3"
    store = SqliteLifecycleStore(db)
    service = RequestLifecycleCoordinator(store)
    results = []

    def check(case_id, title, requirement, fn):
        started = time.perf_counter()
        try:
            detail = fn()
            outcome = "PASS"
        except AssertionError as exc:
            outcome, detail = "FAIL", f"assertion: {exc}"
        except Exception as exc:
            outcome, detail = "FAIL", f"{type(exc).__name__}: {exc}"
        results.append({"id": case_id, "title": title, "requirement": requirement, "result": outcome,
                        "detail": detail, "seconds": round(time.perf_counter() - started, 4)})

    def raises(exc_type, fn):
        try:
            fn()
        except exc_type as exc:
            return str(exc)
        raise AssertionError(f"expected {exc_type.__name__}, nothing raised")

    def integrity():
        for rel, expected in release["files"].items():
            actual = hashlib.sha256((current / rel).read_bytes()).hexdigest()
            assert actual == expected, f"{rel} hash drift"
        assert lifecycle.__file__.startswith(str(current)), "service not loaded from deployed release"
        return f"{len(release['files'])} files match release.json; loaded from {lifecycle.__file__}"

    def schema():
        c = store.connect()
        try:
            tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            assert {"accounts", "requests", "lifecycle_events"} <= tables, tables
            assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert c.execute("PRAGMA foreign_key_check").fetchall() == []
            return "tables present; integrity_check ok; foreign_key_check empty"
        finally:
            c.close()

    journey = {}
    def critical_journey():
        steps = [("Accepted", 0, "Water team accepted the request.", "staff-a", "2026-09-25T12:00:00+00:00"),
                 ("In Progress", 1, "Crew dispatched.", None, None),
                 ("Resolved", 2, "Pipe repaired and pressure restored.", None, None),
                 ("Closed", 3, "Confirmed resolved.", None, None)]
        stamps = ["2026-09-24T09:00:00+00:00", "2026-09-24T10:00:00+00:00", "2026-09-24T11:00:00+00:00", "2026-09-24T12:00:00+00:00"]
        for (target, version, text, assignee, due), stamp in zip(steps, stamps):
            service.clock = lambda s=stamp: s
            out = service.transition("staff-a", "CC-DEMO-001", target, version, text, assignee=assignee, due_at=due)
            assert out["status"] == target and out["version"] == version + 1
            started = time.perf_counter()
            seen = SqliteLifecycleStore(db).history("citizen-a", "CC-DEMO-001")
            journey[target] = round(time.perf_counter() - started, 6)
            assert seen["status"] == target and seen["events"][-1]["explanation"] == text
        final = SqliteLifecycleStore(db).history("citizen-a", "CC-DEMO-001")
        assert [e["to_status"] for e in final["events"]] == ["Accepted", "In Progress", "Resolved", "Closed"]
        assert [e["version"] for e in final["events"]] == [1, 2, 3, 4]
        return f"4 transitions committed; citizen read-after-commit seconds {journey} (targets 5 s FR-05, 60 s FR-08)"

    def restart_persistence():
        code = ("import sys,json;sys.path.insert(0,sys.argv[1]);from lifecycle import SqliteLifecycleStore as S;"
                "h=S(sys.argv[2]).history('citizen-a','CC-DEMO-001');print(json.dumps([h['status'],len(h['events'])]))")
        out = subprocess.run([sys.executable, "-c", code, str(current / "product"), str(db)], capture_output=True, text=True, check=True)
        assert json.loads(out.stdout) == ["Closed", 4], out.stdout
        return "fresh Python process read status Closed with 4 events"

    def rejection_needs_reason():
        service.clock = lambda: "2026-09-24T09:00:00+00:00"
        msg = raises(InvalidTransition, lambda: service.transition("staff-a", "CC-STG-002", "Rejected", 0, "   "))
        h = SqliteLifecycleStore(db).history("citizen-b", "CC-STG-002")
        assert h["status"] == "Submitted" and h["events"] == []
        return f"rejected with '{msg}'; record unchanged"

    def rejection_with_reason():
        out = service.transition("staff-a", "CC-STG-002", "Rejected", 0, "Duplicate of an existing request.")
        h = SqliteLifecycleStore(db).history("citizen-b", "CC-STG-002")
        assert h["status"] == "Rejected" and h["events"][0]["explanation"] == "Duplicate of an existing request."
        return "rejection with reason committed and visible to owner"

    check("ST-01", "Release files match deployed manifest and service loads from release dir", "NFR-06", integrity)
    check("ST-02", "Staging database schema and integrity", "NFR-06 / R-12", schema)
    check("ST-03", "Critical journey: accept, progress, resolve, close; citizen reads status/history", "FR-13, FR-05, FR-08", critical_journey)
    check("ST-04", "Committed state survives process restart", "FR-05 / R-12", restart_persistence)
    check("ST-05", "Citizen B cannot read citizen A's history", "NFR-02", lambda: raises(Forbidden, lambda: store.history("citizen-b", "CC-DEMO-001")))
    check("ST-06", "Wrong-department staff cannot transition", "NFR-02", lambda: raises(Forbidden, lambda: service.transition("staff-b", "CC-STG-002", "Accepted", 0, "x", assignee="staff-b", due_at="2026-09-26T09:00:00+00:00")))
    check("ST-07", "Citizen cannot transition a request", "NFR-02", lambda: raises(Forbidden, lambda: service.transition("citizen-a", "CC-STG-002", "Accepted", 0, "x", assignee="staff-a", due_at="2026-09-26T09:00:00+00:00")))
    check("ST-08", "Deactivated staff account is denied", "NFR-02 / FR-06", lambda: raises(Forbidden, lambda: service.transition("inactive", "CC-STG-002", "Accepted", 0, "x", assignee="staff-a", due_at="2026-09-26T09:00:00+00:00")))
    check("ST-09", "Invalid transition from Closed is rejected", "FR-13", lambda: raises(InvalidTransition, lambda: service.transition("staff-a", "CC-DEMO-001", "Accepted", 4, "again", assignee="staff-a", due_at="2026-09-30T09:00:00+00:00")))
    check("ST-10", "Stale version cannot overwrite", "FR-13 / ASR-L03", lambda: raises(Conflict, lambda: service.transition("staff-a", "CC-DEMO-001", "Closed", 1, "stale")))
    check("ST-11", "Rejection without reason is refused and leaves no record", "FR-13, FR-08", rejection_needs_reason)
    check("ST-12", "Rejection with reason is committed and visible", "FR-13, FR-08", rejection_with_reason)

    def backup_restore():
        backups = root / "backups"
        backup = backups / "staging-backup.sqlite3"
        source = sqlite3.connect(db); target = sqlite3.connect(backup)
        with target: source.backup(target)
        source.close(); target.close()
        with tempfile.TemporaryDirectory() as tmp:
            restored = Path(tmp) / "restored.sqlite3"
            restored.write_bytes(backup.read_bytes())
            r = SqliteLifecycleStore(restored)
            h = r.history("citizen-a", "CC-DEMO-001")
            c = r.connect()
            ok = c.execute("PRAGMA integrity_check").fetchone()[0]
            counts = [c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("accounts", "requests", "lifecycle_events")]
            c.close()
            assert ok == "ok" and h["status"] == "Closed" and len(h["events"]) == 4
        return f"backup restored to scratch copy; integrity ok; row counts accounts/requests/events = {counts}"
    check("ST-13", "Backup and restore reproduces committed data (R-15 experiment)", "R-15 / NFR-04", backup_restore)

    passed = sum(r["result"] == "PASS" for r in results)
    report = {"release_id": release["release_id"], "fingerprint_sha256": release["fingerprint_sha256"],
              "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "python": release["python"], "sqlite": release["sqlite"], "platform": release["platform"],
              "passed": passed, "total": len(results), "results": results}
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    for r in results:
        print(f"{r['id']} {r['result']}  {r['title']}  [{r['requirement']}]")
    print(f"{passed}/{len(results)} passed")
    sys.exit(0 if passed == len(results) else 1)

if __name__ == "__main__":
    main()
