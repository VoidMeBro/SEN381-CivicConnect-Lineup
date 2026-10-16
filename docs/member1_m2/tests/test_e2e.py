"""Critical end-to-end browser-route journeys using synthetic data."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        from test_web_security import WebSecurityTests
        WebSecurityTests.setUp(self)

    def call(self, *args, **kwargs):
        from test_web_security import WebSecurityTests
        return WebSecurityTests.call(self, *args, **kwargs)

    def sign_in(self, *args, **kwargs):
        from test_web_security import WebSecurityTests
        return WebSecurityTests.sign_in(self, *args, **kwargs)

    def run_citizen_staff_management_journey(self):
        from test_web_security import WebSecurityTests
        WebSecurityTests.run_citizen_staff_management_journey(self)

    def test_E2E_citizen_to_staff_to_management_journey(self):
        self.store.bootstrap_administrator("admin", "AdminPass-381!", "2026-10-01T10:00:00+00:00")
        self.run_citizen_staff_management_journey()

    def test_E2E_staff_finishes_lifecycle_and_citizen_sees_completion(self):
        from test_web_security import WebSecurityTests
        WebSecurityTests.test_citizen_submission_staff_lifecycle_and_requester_history(self)

    def test_E2E_citizen_can_reopen_unresolved_work_then_confirm_closure(self):
        import re
        from web import CivicConnectWeb

        app = CivicConnectWeb(self.store, "R" * 48)
        reference = "CC-DEMO-001"
        citizen = self.sign_in(app, "citizen-a")
        staff = self.sign_in(app, "staff-a")

        for version, target, explanation, assignee, due_at in [
            (0, "Accepted", "Water team accepted the work.", "staff-a", "2026-10-20T12:00"),
            (1, "In Progress", "Repair work started.", "", ""),
            (2, "Resolved", "Repair completed and checked.", "", ""),
        ]:
            _, _, detail = self.call(app, f"/requests/{reference}", cookie=staff)
            csrf = re.search(r'name="csrf" value="([^"]+)"', detail).group(1)
            status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", staff, {
                "csrf": csrf, "version": str(version), "target": target,
                "explanation": explanation, "assignee": assignee, "due_at": due_at,
            })
            self.assertTrue(status.startswith("303"))

        _, _, review = self.call(app, f"/requests/{reference}", cookie=citizen)
        self.assertIn("No, it is not resolved", review)
        self.assertIn("Yes, close request", review)
        csrf = re.search(r'name="csrf" value="([^"]+)"', review).group(1)
        status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", citizen, {
            "csrf": csrf, "version": "3", "target": "In Progress",
            "explanation": "The pipe is still leaking after the repair.",
        })
        self.assertTrue(status.startswith("303"))
        history = self.store.history("citizen-a", reference)
        self.assertEqual(history["status"], "In Progress")
        self.assertEqual(history["events"][-1]["explanation"], "The pipe is still leaking after the repair.")

        _, _, detail = self.call(app, f"/requests/{reference}", cookie=staff)
        csrf = re.search(r'name="csrf" value="([^"]+)"', detail).group(1)
        status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", staff, {
            "csrf": csrf, "version": "4", "target": "Resolved",
            "explanation": "Leak repaired and inspected again.",
        })
        self.assertTrue(status.startswith("303"))

        _, _, review = self.call(app, f"/requests/{reference}", cookie=citizen)
        csrf = re.search(r'name="csrf" value="([^"]+)"', review).group(1)
        status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", citizen, {
            "csrf": csrf, "version": "5", "target": "Closed",
        })
        self.assertTrue(status.startswith("303"))
        self.assertEqual(self.store.history("citizen-a", reference)["status"], "Closed")

    def test_E2E_other_citizen_cannot_confirm_or_reopen_resolved_request(self):
        import re
        from web import CivicConnectWeb

        app = CivicConnectWeb(self.store, "A" * 48)
        reference = "CC-DEMO-001"
        staff = self.sign_in(app, "staff-a")
        for version, target, explanation, assignee, due_at in [
            (0, "Accepted", "Water team accepted the work.", "staff-a", "2026-10-20T12:00"),
            (1, "In Progress", "Repair work started.", "", ""),
            (2, "Resolved", "Repair completed and checked.", "", ""),
        ]:
            _, _, detail = self.call(app, f"/requests/{reference}", cookie=staff)
            csrf = re.search(r'name="csrf" value="([^"]+)"', detail).group(1)
            status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", staff, {
                "csrf": csrf, "version": str(version), "target": target,
                "explanation": explanation, "assignee": assignee, "due_at": due_at,
            })
            self.assertTrue(status.startswith("303"))

        other = self.sign_in(app, "citizen-b")
        status, _, page = self.call(app, f"/requests/{reference}", cookie=other)
        self.assertTrue(status.startswith("403"))
        _, _, own_requests = self.call(app, "/requests", cookie=other)
        csrf = re.search(r'name="csrf" value="([^"]+)"', own_requests).group(1)
        status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", other, {
            "csrf": csrf, "version": "3", "target": "Closed",
        })
        self.assertTrue(status.startswith("403"))
        self.assertEqual(self.store.history("citizen-a", reference)["status"], "Resolved")



if __name__ == "__main__":
    unittest.main()
