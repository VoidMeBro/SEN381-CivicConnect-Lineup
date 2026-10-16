"""Small robustness probe: malformed inputs against the DEPLOYED service on a scratch database.
Records which exception type each input produces. Domain errors (Forbidden, Conflict, InvalidTransition) are the documented contract."""
import json, os, sys, tempfile
from pathlib import Path
root = Path(sys.argv[1]).resolve(); out = sys.argv[2]
if os.environ.get("CIVICCONNECT_ENV") != "staging": sys.exit("Set CIVICCONNECT_ENV=staging")
sys.path.insert(0, str(root / "current" / "product"))
from lifecycle import SqliteLifecycleStore, RequestLifecycleCoordinator, seed_demo, Forbidden, Conflict, InvalidTransition
DOMAIN = (Forbidden, Conflict, InvalidTransition)
rows = []
with tempfile.TemporaryDirectory() as tmp:
    store = SqliteLifecycleStore(Path(tmp) / "probe.sqlite3"); store.initialise(); seed_demo(store)
    svc = RequestLifecycleCoordinator(store, clock=lambda: "2026-09-24T09:00:00+00:00")
    ok_due = "2026-09-25T12:00:00+00:00"
    cases = {
      "history actor None": lambda: store.history(None, "CC-DEMO-001"),
      "history reference None": lambda: store.history("citizen-a", None),
      "history reference list": lambda: store.history("citizen-a", ["CC-DEMO-001"]),
      "history actor int": lambda: store.history(123, "CC-DEMO-001"),
      "transition reference list": lambda: svc.transition("staff-a", ["x"], "Accepted", 0, "t", assignee="staff-a", due_at=ok_due),
      "transition target None": lambda: svc.transition("staff-a", "CC-DEMO-001", None, 0, "t"),
      "transition version str": lambda: svc.transition("staff-a", "CC-DEMO-001", "Accepted", "0", "t", assignee="staff-a", due_at=ok_due),
      "transition version bool": lambda: svc.transition("staff-a", "CC-DEMO-001", "Accepted", False, "t", assignee="staff-a", due_at=ok_due),
      "transition explanation None": lambda: svc.transition("staff-a", "CC-DEMO-001", "Accepted", 0, None, assignee="staff-a", due_at=ok_due),
      "transition assignee list": lambda: svc.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "t", assignee=["staff-a"], due_at=ok_due),
      "transition due_at not a date": lambda: svc.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "t", assignee="staff-a", due_at="tomorrow"),
      "transition due_at naive": lambda: svc.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "t", assignee="staff-a", due_at="2026-09-25T12:00:00"),
      "transition due before submission": lambda: svc.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "t", assignee="staff-a", due_at="2026-09-23T12:00:00+00:00"),
    }
    for name, fn in cases.items():
        try:
            fn(); rows.append({"input": name, "outcome": "accepted"})
        except DOMAIN as exc:
            rows.append({"input": name, "outcome": "domain error", "type": type(exc).__name__, "message": str(exc)})
        except Exception as exc:
            rows.append({"input": name, "outcome": "RAW EXCEPTION", "type": type(exc).__module__ + "." + type(exc).__name__, "message": str(exc)[:120]})
Path(out).write_text(json.dumps(rows, indent=2), encoding="utf-8")
for r in rows: print(f"{r['outcome']:14} {r['input']:36} {r.get('type','')}")
