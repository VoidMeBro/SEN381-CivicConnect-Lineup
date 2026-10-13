"""Focused component checks for lifecycle policy and persistence invariants."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "product"))
from lifecycle import InvalidTransition, LifecyclePolicy, SqliteLifecycleStore, RequestLifecycleCoordinator

TEST_TMP = Path(__file__).resolve().parents[1] / ".test-tmp"
TEST_TMP.mkdir(exist_ok=True)


class ComponentTests(unittest.TestCase):
    def test_transition_policy_rejects_skipped_status(self):
        request = {"status": "Submitted", "submitted_at": "2026-10-01T10:00:00+00:00"}
        with self.assertRaises(InvalidTransition):
            LifecyclePolicy.check(request, "Resolved", "Done", None, None)

    def test_transition_policy_requires_acceptance_assignee_and_due_time(self):
        request = {"status": "Submitted", "submitted_at": "2026-10-01T10:00:00+00:00"}
        with self.assertRaises(InvalidTransition):
            LifecyclePolicy.check(request, "Accepted", "Accepted", None, None)

    def test_transition_policy_requires_rejection_reason(self):
        request = {"status": "Submitted", "submitted_at": "2026-10-01T10:00:00+00:00"}
        with self.assertRaises(InvalidTransition):
            LifecyclePolicy.check(request, "Rejected", "  ", None, None)

    def test_transition_policy_rejects_due_date_before_submission(self):
        request = {"status": "Submitted", "submitted_at": "2026-10-01T10:00:00+00:00"}
        with self.assertRaises(InvalidTransition):
            LifecyclePolicy.check(request, "Accepted", "Accepted", "staff-a", "2026-10-01T09:59:00+00:00")

    def test_invalid_transition_keeps_request_and_event_count_unchanged(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as directory:
            store = SqliteLifecycleStore(Path(directory) / "component.sqlite3")
            store.initialise()
            store.register_citizen("citizen", "CitizenPass-381!", "2026-10-01T10:00:00+00:00")
            store.bootstrap_administrator("admin", "AdminPass-381!", "2026-10-01T10:00:00+00:00")
            store.manage_account("admin", "staff", "Staff", "Water", "1", "StaffPass-381!", "2026-10-01T10:00:00+00:00")
            reference = store.submit_request("citizen", "Blocked drain", "The drain near the park is blocked.", "Park Road", "water", "2026-10-01T10:00:00+00:00")
            service = RequestLifecycleCoordinator(store, clock=lambda: "2026-10-01T11:00:00+00:00")
            with self.assertRaises(InvalidTransition):
                service.transition("staff", reference, "Resolved", 0, "Skipped steps")
            detail = store.history("citizen", reference)
            self.assertEqual(detail["status"], "Submitted")
            self.assertEqual(detail["events"], [])


if __name__ == "__main__":
    unittest.main()
