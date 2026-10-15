import sqlite3
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'product'))
from lifecycle import SqliteLifecycleStore,RequestLifecycleCoordinator,seed_demo,Forbidden,Conflict,InvalidTransition

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.store=SqliteLifecycleStore(Path(temporary.name)/'test.sqlite3')
        self.store.initialise();seed_demo(self.store)
        self.service=RequestLifecycleCoordinator(self.store,clock=lambda:'2026-09-24T09:00:00+00:00')
    def accept(self,**changes):
        args=dict(actor_id='staff-a',reference='CC-DEMO-001',target='Accepted',expected_version=0,
                  explanation='Assigned to the water team.',assignee='staff-a',due_at='2026-09-25T12:00:00+00:00')
        args.update(changes);return self.service.transition(**args)
    def unchanged(self):
        result=self.store.history('citizen-a','CC-DEMO-001')
        self.assertEqual((result['status'],result['version'],result['events']),('Submitted',0,[]))
    def sql(self,query,args=()):
        c=self.store.connect()
        try:
            with c:return c.execute(query,args).fetchall()
        finally:c.close()
    def test_FR13_acceptance_commits_status_and_event(self):
        self.accept();h=SqliteLifecycleStore(self.store.path).history('citizen-a','CC-DEMO-001')
        self.assertEqual((h['status'],h['version'],len(h['events'])),('Accepted',1,1))
        self.assertEqual(h['events'][0]['actor'],'staff-a')
        self.assertEqual(h['events'][0]['occurred_at'],'2026-09-24T09:00:00+00:00')
    def test_FR13_acceptance_requires_assignee(self):
        with self.assertRaises(InvalidTransition):self.accept(assignee=None)
        self.unchanged()
    def test_FR13_acceptance_requires_due_time(self):
        with self.assertRaises(InvalidTransition):self.accept(due_at=None)
        self.unchanged()
    def test_FR13_due_time_must_follow_submission(self):
        with self.assertRaises(InvalidTransition):self.accept(due_at='2026-09-24T07:00:00+00:00')
        self.unchanged()
    def test_FR13_rejects_naive_timestamp(self):
        with self.assertRaises(InvalidTransition):self.accept(due_at='2026-09-25T12:00:00')
        self.unchanged()
    def test_FR13_rejects_wrong_department_assignee(self):
        with self.assertRaises(InvalidTransition):self.accept(assignee='staff-b')
        self.unchanged()
    def test_FR13_rejects_inactive_assignee(self):
        with self.assertRaises(InvalidTransition):self.accept(assignee='inactive')
        self.unchanged()
    def test_FR13_rejects_invalid_transition(self):
        with self.assertRaises(InvalidTransition):self.accept(target='Closed')
        self.unchanged()
    def test_NFR02_other_department_denied(self):
        with self.assertRaises(Forbidden):self.accept(actor_id='staff-b')
        self.unchanged()
    def test_NFR02_citizen_cannot_transition(self):
        with self.assertRaises(Forbidden):self.accept(actor_id='citizen-a')
        self.unchanged()
    def test_NFR02_deactivation_applies_on_next_call(self):
        self.sql('UPDATE accounts SET active=0 WHERE id=?',('staff-a',))
        with self.assertRaises(Forbidden):self.accept()
        self.unchanged()
    def test_NFR02_non_owner_cannot_read_history(self):
        self.accept()
        with self.assertRaises(Forbidden):self.store.history('citizen-b','CC-DEMO-001')
    def test_FR08_rejection_requires_explanation(self):
        with self.assertRaises(InvalidTransition):
            self.service.transition('staff-a','CC-DEMO-001','Rejected',0,' ')
        self.unchanged()
    def test_FR08_rejection_feedback_is_committed(self):
        self.service.transition('staff-a','CC-DEMO-001','Rejected',0,'Outside service area')
        self.assertEqual(self.store.history('citizen-a','CC-DEMO-001')['events'][0]['explanation'],'Outside service area')
        with self.assertRaises(InvalidTransition):
            self.service.transition('staff-a','CC-DEMO-001','Accepted',1)
    def test_FR13_complete_lifecycle_and_resolution_summary(self):
        self.accept()
        self.service.transition('staff-a','CC-DEMO-001','In Progress',1)
        with self.assertRaises(InvalidTransition):self.service.transition('staff-a','CC-DEMO-001','Resolved',2)
        self.service.transition('staff-a','CC-DEMO-001','Resolved',2,'Leak repaired')
        self.service.transition('staff-a','CC-DEMO-001','Closed',3)
        h=self.store.history('citizen-a','CC-DEMO-001')
        self.assertEqual((h['status'],len(h['events'])),('Closed',4))
        self.assertEqual(h['events'][2]['explanation'],'Leak repaired')
        with self.assertRaises(InvalidTransition):self.service.transition('staff-a','CC-DEMO-001','Accepted',4)
    def test_FR05_history_failure_rolls_back_status(self):
        self.sql("CREATE TRIGGER fail_history BEFORE INSERT ON lifecycle_events BEGIN SELECT RAISE(ABORT,'simulated history failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.accept()
        self.unchanged()
    def test_FR13_stale_version_cannot_overwrite(self):
        self.accept()
        with self.assertRaises(Conflict):self.accept()
        self.assertEqual(len(self.store.history('citizen-a','CC-DEMO-001')['events']),1)
    def test_FR13_competing_updates_have_one_winner(self):
        def attempt(_):
            try:self.accept();return 'saved'
            except Conflict:return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(attempt,range(2)))
        self.assertCountEqual(outcomes,['saved','conflict'])
        self.assertEqual(len(self.store.history('citizen-a','CC-DEMO-001')['events']),1)
    def test_database_rejects_invalid_status(self):
        with self.assertRaises(sqlite3.IntegrityError):self.sql("UPDATE requests SET status='Unknown'")
        self.unchanged()
    def test_database_rejects_orphan_event(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.sql("INSERT INTO lifecycle_events VALUES(1,'missing','Submitted','Rejected','staff-a','2026-09-24T09:00:00+00:00','reason',1)")
        self.unchanged()

if __name__=='__main__':unittest.main()
