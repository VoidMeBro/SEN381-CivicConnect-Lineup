"""Run the actual Submitted -> Accepted -> requester history path offline."""
import json
from pathlib import Path
import tempfile
import time
from lifecycle import SqliteLifecycleStore,RequestLifecycleCoordinator,seed_demo

def main():
    with tempfile.TemporaryDirectory(prefix='civicconnect-demo-') as directory:
        store=SqliteLifecycleStore(Path(directory)/'demo.sqlite3')
        store.initialise();seed_demo(store)
        service=RequestLifecycleCoordinator(store,clock=lambda:'2026-09-24T09:00:00+00:00')
        result=service.transition('staff-a','CC-DEMO-001','Accepted',0,
                                  'Water team accepted the request.',assignee='staff-a',
                                  due_at='2026-09-25T12:00:00+00:00')
        started=time.perf_counter()
        # Re-open the DB through a separate store instance to verify committed state.
        history=SqliteLifecycleStore(store.path).history('citizen-a','CC-DEMO-001')
        elapsed=time.perf_counter()-started
        assert history['status']=='Accepted' and len(history['events'])==1
        assert history['events'][0]['explanation']==result['explanation']
        print(json.dumps({'trace':'FR-13 -> ASR-L01 -> coordinator/policy -> atomic SQLite transaction -> in-process interface -> ADR-M1-02 -> lifecycle.py -> tests/test_lifecycle.py',
                          'transition':result,'requester_history':history,'local_post_commit_read_seconds':round(elapsed,6),
                          'scope':'Executed local service path using synthetic data. Browser authentication, production stack and deployed 5/60-second UI targets are outside this run.'},indent=2))

if __name__=='__main__':main()
