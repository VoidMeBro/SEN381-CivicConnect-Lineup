"""Service, persistence and browser-route integration checks."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "product"))
from lifecycle import Forbidden, RequestLifecycleCoordinator, SqliteLifecycleStore, seed_demo

TEST_TMP = Path(__file__).resolve().parents[1] / ".test-tmp"
TEST_TMP.mkdir(exist_ok=True)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TMP)
        self.addCleanup(self.temp.cleanup)
        self.store = SqliteLifecycleStore(Path(self.temp.name) / "integration.sqlite3")
        self.store.initialise()
        seed_demo(self.store, "LocalDemo-381-2026!")
        self.store.bootstrap_administrator("admin", "AdminPass-381!", "2026-10-01T10:00:00+00:00")

    def test_FR13_committed_transition_updates_both_current_state_and_history(self):
        service = RequestLifecycleCoordinator(self.store, clock=lambda: "2026-09-24T09:00:00+00:00")
        service.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "Water team accepted the request.", "staff-a", "2026-09-25T12:00:00+00:00")
        reopened = SqliteLifecycleStore(self.store.path).history("citizen-a", "CC-DEMO-001")
        self.assertEqual(reopened["status"], "Accepted")
        self.assertEqual(reopened["events"][0]["actor"], "staff-a")

    def test_FR12_assignment_to_another_department_is_rejected_without_change(self):
        service = RequestLifecycleCoordinator(self.store, clock=lambda: "2026-09-24T09:00:00+00:00")
        from lifecycle import InvalidTransition
        with self.assertRaises(InvalidTransition):
            service.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "Wrong assignee.", "staff-b", "2026-09-25T12:00:00+00:00")
        self.assertEqual(self.store.history("citizen-a", "CC-DEMO-001")["status"], "Submitted")

    def test_FR11_username_assignee_filter_maps_to_account_id_safely(self):
        service = RequestLifecycleCoordinator(self.store, clock=lambda: "2026-10-14T09:00:00+00:00")
        service.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "Assigned.", "staff-a", "2026-10-15T12:00:00+00:00")
        result = self.store.list_staff_requests("staff-a", assignee="STAFF-A")
        self.assertEqual([item["reference"] for item in result], ["CC-DEMO-001"])

    def test_FR11_inactive_assignee_filter_is_rejected(self):
        from lifecycle import InvalidTransition
        with self.assertRaises(InvalidTransition):
            self.store.list_staff_requests("staff-a", assignee="inactive")

    def test_FR11_due_date_sort_places_earliest_due_first(self):
        service = RequestLifecycleCoordinator(self.store, clock=lambda: "2026-10-14T09:00:00+00:00")
        service.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "Assigned.", "staff-a", "2026-10-15T12:00:00+00:00")
        first = self.store.submit_request("citizen-a", "Water leak", "A second request for sort validation.", "Park Road", "water", "2026-10-03T00:00:00+00:00")
        service.transition("staff-a", first, "Accepted", 0, "Assigned later.", "staff-a", "2026-10-20T12:00:00+00:00")
        sorted_rows = self.store.list_staff_requests("staff-a", sort="due", direction="asc")
        self.assertEqual([row["reference"] for row in sorted_rows[:2]], ["CC-DEMO-001", first])

    def test_FR09_report_date_bounds_include_end_date_and_exclude_later_records(self):
        self.store.submit_request("citizen-a", "Road damage", "A report boundary test request.", "Main Road", "roads", "2026-10-03T00:00:00+00:00")
        self.store.manage_account("admin", "manager", "Management", "", "1", "ManagerPass-381!", "2026-10-01T10:00:00+00:00")
        report = self.store.management_summary("manager", date_from="2026-10-03", date_to="2026-10-03")
        self.assertEqual(len(report["requests"]), 1)


if __name__ == "__main__":
    unittest.main()
