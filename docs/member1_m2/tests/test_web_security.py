"""Route-level authorization and first-administrator setup checks."""

from html.parser import HTMLParser
import io
from pathlib import Path
import re
import sys
import tempfile
import unittest
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "product"))
from lifecycle import SqliteLifecycleStore, seed_demo
from web import CivicConnectWeb

TEST_TMP = Path(__file__).resolve().parents[1] / ".test-tmp"
TEST_TMP.mkdir(exist_ok=True)


class WebSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TMP)
        self.addCleanup(self.temp.cleanup)
        self.store = SqliteLifecycleStore(Path(self.temp.name) / "web.sqlite3")
        self.store.initialise()
        seed_demo(self.store, "LocalDemo-381-2026!")

    def call(self, app, path, method="GET", cookie="", form=None, remote="127.0.0.1"):
        body = urlencode(form or {}).encode("utf-8") if form is not None else b""
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
            "HTTP_COOKIE": cookie,
            "REMOTE_ADDR": remote,
        }
        result = {}
        payload = b"".join(app(environ, lambda status, headers: result.update(status=status, headers=dict(headers))))
        return result["status"], result["headers"], payload.decode("utf-8")

    def sign_in(self, app, username, password="LocalDemo-381-2026!"):
        status, headers, body = self.call(app, "/login")
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        csrf = re.search(r'name="csrf" value="([^"]+)"', body).group(1)
        status, headers, _ = self.call(app, "/login", "POST", cookie, {
            "csrf": csrf, "username": username, "password": password,
        })
        self.assertTrue(status.startswith("303"))
        return headers["Set-Cookie"].split(";", 1)[0]

    def test_admin_setup_requires_private_token_and_closes_after_first_admin(self):
        no_token = CivicConnectWeb(self.store, "S" * 48)
        self.assertTrue(self.call(no_token, "/setup/administrator")[0].startswith("403"))
        secret = "Private-Admin-Setup-Token-381-2026"
        app = CivicConnectWeb(self.store, "S" * 48, admin_setup_token=secret)
        status, headers, body = self.call(app, "/setup/administrator")
        self.assertTrue(status.startswith("200"))
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        csrf = re.search(r'name="csrf" value="([^"]+)"', body).group(1)
        bad = {"csrf": csrf, "username": "admin-web", "password": "AdminWebPass-381!", "setup_token": "wrong-token"}
        self.assertTrue(self.call(app, "/setup/administrator", "POST", cookie, bad)[0].startswith("403"))
        good = dict(bad, setup_token=secret)
        status, _, _ = self.call(app, "/setup/administrator", "POST", cookie, good)
        self.assertTrue(status.startswith("303"))
        self.assertEqual(self.store.authenticate("admin-web", "AdminWebPass-381!")["role"], "Administrator")
        self.assertTrue(self.call(app, "/setup/administrator")[0].startswith("403"))

    def test_existing_administrator_keeps_bootstrap_endpoint_closed(self):
        self.store.bootstrap_administrator("existing-admin", "ExistingAdminPass-381!", "2026-10-01T10:00:00+00:00")
        app = CivicConnectWeb(self.store, "S" * 48, admin_setup_token="Private-Admin-Setup-Token-381-2026")
        self.assertTrue(self.call(app, "/setup/administrator")[0].startswith("403"))

    def test_staff_and_citizen_cannot_open_admin_routes(self):
        app = CivicConnectWeb(self.store, "S" * 48)
        for username in ("staff-a", "citizen-a"):
            status, headers, body = self.call(app, "/login")
            cookie = headers["Set-Cookie"].split(";", 1)[0]
            csrf = re.search(r'name="csrf" value="([^"]+)"', body).group(1)
            status, headers, _ = self.call(app, "/login", "POST", cookie, {
                "csrf": csrf, "username": username, "password": "LocalDemo-381-2026!",
            })
            cookie = headers["Set-Cookie"].split(";", 1)[0]
            self.assertTrue(self.call(app, "/admin/accounts", cookie=cookie)[0].startswith("403"))
            self.assertTrue(self.call(app, "/admin/categories", cookie=cookie)[0].startswith("403"))

    def test_citizen_submission_staff_lifecycle_and_requester_history(self):
        app = CivicConnectWeb(self.store, "W" * 48)
        citizen = self.sign_in(app, "citizen-a")
        _, _, form = self.call(app, "/requests/new", cookie=citizen)
        csrf = re.search(r'name="csrf" value="([^"]+)"', form).group(1)
        status, _, _ = self.call(app, "/requests", "POST", citizen, {
            "csrf": csrf, "title": "Blocked drain near stop", "description": "Drain is blocked by debris near the bus stop.",
            "location": "Central bus stop", "category_id": "water",
        })
        self.assertTrue(status.startswith("303"))
        # New requests appear in the citizen list and have a routable reference.
        _, _, listing = self.call(app, "/requests", cookie=citizen)
        match = re.search(r'href="(/requests/(CC-[A-Z0-9-]+))"', listing)
        self.assertIsNotNone(match)
        reference = match.group(2)
        self.assertEqual(self.call(app, "/requests/" + reference, cookie=citizen)[0], "200 OK")
        staff = self.sign_in(app, "staff-a")
        status, _, staff_detail = self.call(app, "/requests/" + reference, cookie=staff)
        self.assertEqual(status, "200 OK")
        self.assertIn('action="/requests/' + reference + '/transition"', staff_detail)
        for version, target, explanation, assignee, due in [
            (0, "Accepted", "Water team accepted the request.", "staff-a", "2026-10-20T12:00"),
            (1, "In Progress", "Repair work started.", "", ""),
            (2, "Resolved", "Drain cleared and inspected.", "", ""),
            (3, "Closed", "Completion confirmed.", "", ""),
        ]:
            _, _, page = self.call(app, "/requests/" + reference, cookie=staff)
            csrf = re.search(r'name="csrf" value="([^"]+)"', page).group(1)
            status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", staff, {
                "csrf": csrf, "version": str(version), "target": target, "explanation": explanation,
                "assignee": assignee, "due_at": due,
            })
            self.assertTrue(status.startswith("303"))
        _, _, citizen_detail = self.call(app, "/requests/" + reference, cookie=citizen)
        self.assertIn("Closed", citizen_detail)
        self.assertIn("Drain cleared and inspected.", citizen_detail)

    def run_citizen_staff_management_journey(self):
        self.store.register_citizen("citizen-new", "CitizenNewPass-381!", "2026-10-01T10:00:00+00:00")
        self.store.manage_account("admin", "manager-new", "Management", "", "1", "ManagerNewPass-381!", "2026-10-01T10:00:00+00:00")
        self.store.manage_account("admin", "staff-new", "Staff", "Water", "1", "StaffNewPass-381!", "2026-10-01T10:00:00+00:00")
        app = CivicConnectWeb(self.store, "E" * 48)
        citizen = self.sign_in(app, "citizen-new", "CitizenNewPass-381!")
        _, _, form_page = self.call(app, "/requests/new", cookie=citizen)
        csrf = re.search(r'name="csrf" value="([^"]+)"', form_page).group(1)
        status, _, _ = self.call(app, "/requests", "POST", citizen, {
            "csrf": csrf, "title": "Water leak", "description": "Water is leaking next to the public library.",
            "location": "Library entrance", "category_id": "water",
        })
        self.assertTrue(status.startswith("303"))
        _, _, listing = self.call(app, "/requests", cookie=citizen)
        reference = re.search(r'href="/requests/(CC-[A-Z0-9-]+)"', listing).group(1)
        staff = self.sign_in(app, "staff-new", "StaffNewPass-381!")
        status, _, detail = self.call(app, "/requests/" + reference, cookie=staff)
        self.assertEqual(status, "200 OK")
        csrf = re.search(r'name="csrf" value="([^"]+)"', detail).group(1)
        status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", staff, {
            "csrf": csrf, "version": "0", "target": "Accepted", "explanation": "Water team accepted the request.",
            "assignee": "staff-new", "due_at": "2026-10-20T12:00",
        })
        self.assertTrue(status.startswith("303"))
        manager = self.sign_in(app, "manager-new", "ManagerNewPass-381!")
        status, _, report = self.call(app, "/management/summary", cookie=manager)
        self.assertEqual(status, "200 OK")
        self.assertIn(reference, report)
        self.assertIn("Accepted", report)

    def test_e2e_admin_configures_and_citizen_submits_staff_accepts_management_reports(self):
        self.store.bootstrap_administrator("admin", "AdminPass-381!", "2026-10-01T10:00:00+00:00")
        self.run_citizen_staff_management_journey()

    def test_cross_citizen_denial_csrf_and_html_escaping(self):
        app = CivicConnectWeb(self.store, "W" * 48)
        citizen = self.sign_in(app, "citizen-a")
        _, _, form = self.call(app, "/requests/new", cookie=citizen)
        csrf = re.search(r'name="csrf" value="([^"]+)"', form).group(1)
        self.call(app, "/requests", "POST", citizen, {
            "csrf": csrf, "title": "<script>alert(1)</script>", "description": "A test request includes harmless markup.",
            "location": "Central stop", "category_id": "water",
        })
        _, _, listing = self.call(app, "/requests", cookie=citizen)
        reference = re.search(r'href="/requests/(CC-[A-Z0-9-]+)"', listing).group(1)
        _, _, detail = self.call(app, "/requests/" + reference, cookie=citizen)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", detail)
        self.assertNotIn("<script>alert(1)</script>", detail)
        other = self.sign_in(app, "citizen-b")
        self.assertTrue(self.call(app, "/requests/" + reference, cookie=other)[0].startswith("403"))
        staff = self.sign_in(app, "staff-a")
        status, _, _ = self.call(app, f"/requests/{reference}/transition", "POST", staff, {
            "version": "0", "target": "Accepted", "explanation": "No CSRF value.",
            "assignee": "staff-a", "due_at": "2026-10-20T12:00",
        })
        self.assertTrue(status.startswith("400"))
        self.assertEqual(self.store.history("citizen-a", reference)["status"], "Submitted")


if __name__ == "__main__":
    unittest.main()
