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



if __name__ == "__main__":
    unittest.main()
