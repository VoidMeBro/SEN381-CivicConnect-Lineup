"""Requirement-linked checks for account, category, staff and management flows."""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "product"))
from lifecycle import Forbidden, InvalidTransition, RequestLifecycleCoordinator, SqliteLifecycleStore, seed_demo

TEST_TMP = Path(__file__).resolve().parents[1] / ".test-tmp"
TEST_TMP.mkdir(exist_ok=True)


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TMP)
        self.addCleanup(self.temp.cleanup)
        self.store = SqliteLifecycleStore(Path(self.temp.name) / "features.sqlite3")
        self.store.initialise()
        self.store.register_citizen("citizen-x", "CitizenPass-381!", "2026-10-13T10:00:00+00:00")
        self.store.bootstrap_administrator("admin-x", "AdminPass-381!", "2026-10-13T10:00:00+00:00")
        self.store.manage_account("admin-x", "manager-x", "Management", "", "1", "ManagerPass-381!", "2026-10-13T10:00:00+00:00")
        seed_demo(self.store, "LocalDemo-381-2026!")

    def test_FR06_administrator_creates_and_updates_accounts(self):
        self.store.manage_account("admin-x", "staff-new", "Staff", "Water", "1", "StaffPass-381!", "2026-10-13T10:00:00+00:00")
        self.assertEqual(self.store.authenticate("staff-new", "StaffPass-381!")["role"], "Staff")
        self.store.manage_account("admin-x", "staff-new", "Staff", "Roads", "0", "", "2026-10-13T10:00:00+00:00")
        self.assertIsNone(self.store.authenticate("staff-new", "StaffPass-381!"))

    def test_FR06_non_admin_cannot_manage_accounts(self):
        with self.assertRaises(Forbidden):
            self.store.manage_account("citizen-x", "intruder", "Administrator", "", "1", "IntruderPass-381!", "2026-10-13T10:00:00+00:00")

    def test_FR06_last_active_administrator_cannot_be_removed(self):
        with self.assertRaises(InvalidTransition):
            self.store.manage_account("admin-x", "admin-x", "Staff", "Water", "1", "", "2026-10-13T10:00:00+00:00")
        self.assertEqual(self.store.authenticate_session("admin-x")["role"], "Administrator")

    def test_FR10_category_retirement_preserves_request_label(self):
        reference = self.store.submit_request("citizen-x", "Road damage", "A test request about road damage.", "Main Road", "roads", "2026-10-13T10:00:00+00:00")
        self.store.manage_category("admin-x", "roads", "Roads", "Roads", "0")
        self.assertNotIn("roads", {category["id"] for category in self.store.categories()})
        with self.assertRaises(InvalidTransition):
            self.store.submit_request("citizen-x", "Road damage", "A test request about road damage.", "Main Road", "roads", "2026-10-13T10:00:00+00:00")
        self.assertEqual(self.store.history("citizen-x", reference)["request"]["category_label"], "Roads")

    def test_FR11_staff_search_is_department_scoped_and_literal(self):
        road_ref = self.store.submit_request("citizen-x", "Road 100% damage", "A test request about road damage.", "Main Road", "roads", "2026-10-13T10:00:00+00:00")
        self.assertEqual(self.store.list_staff_requests("staff-b", query="100%")[0]["reference"], road_ref)
        self.assertEqual(self.store.list_staff_requests("staff-a", query="100%"), [])
        self.assertEqual(self.store.list_staff_requests("staff-b", status="Submitted")[0]["reference"], road_ref)

    def test_FR09_management_summary_and_role_gate(self):
        self.store.submit_request("citizen-x", "Road damage", "A test request about road damage.", "Main Road", "roads", "2026-10-13T10:00:00+00:00")
        summary = self.store.management_summary("manager-x", category="roads", status="Submitted")
        self.assertEqual(summary["counts"], {"Submitted": 1})
        self.assertEqual(summary["open_count"], 1)
        self.assertEqual(summary["requests"][0]["citizen_id"], "citizen-x")
        with self.assertRaises(Forbidden):
            self.store.management_summary("citizen-x")

    def test_FR09_open_and_overdue_definitions(self):
        service = RequestLifecycleCoordinator(self.store, clock=lambda: "2026-09-24T09:00:00+00:00")
        service.transition("staff-a", "CC-DEMO-001", "Accepted", 0, "Assigned to water.", "staff-a", "2026-09-25T12:00:00+00:00")
        summary = self.store.management_summary("manager-x")
        self.assertEqual(summary["open_count"], 1)
        self.assertEqual(summary["overdue_count"], 1)
        self.assertEqual(summary["counts"], {"Accepted": 1})

    def test_initial_admin_setup_is_closed_after_admin_creation(self):
        self.assertFalse(self.store.needs_admin_setup())
        with self.assertRaises(Forbidden):
            self.store.bootstrap_administrator("second-admin", "SecondAdminPass-381!", "2026-10-13T10:00:00+00:00")


class ExistingSchemaMigrationTests(unittest.TestCase):
    def test_existing_accounts_and_foreign_keys_survive_management_role_migration(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as directory:
            path = Path(directory) / "old.sqlite3"
            db = sqlite3.connect(path)
            schema = (Path(__file__).resolve().parents[1] / "product" / "schema.sql").read_text(encoding="utf-8")
            db.executescript(schema.replace("'Citizen','Staff','Administrator','Management'", "'Citizen','Staff','Administrator'"))
            db.execute("INSERT INTO accounts VALUES('citizen-old','Citizen','',1)")
            db.execute("INSERT INTO credentials VALUES('citizen-old','citizen-old','pbkdf2_sha256$310000$00$00','2026-10-13T10:00:00+00:00')")
            db.execute("INSERT INTO categories VALUES('water','Water','Water',1)")
            db.execute("INSERT INTO requests(reference,citizen_id,department,status,submitted_at,title,description,location,category_id,category_label) VALUES('CC-OLD-001','citizen-old','Water','Submitted','2026-10-13T10:00:00+00:00','Existing request','Preserve this history.','Main Road','water','Water')")
            db.commit()
            db.close()
            store = SqliteLifecycleStore(path)
            store.initialise()
            db = store.connect()
            try:
                roles = {row["role"] for row in db.execute("SELECT role FROM accounts")}
                self.assertEqual(roles, {"Citizen"})
                self.assertTrue(db.execute("PRAGMA foreign_key_check").fetchall() == [])
                db.execute("INSERT INTO accounts VALUES('manager-old','Management','',1)")
                db.commit()
            finally:
                db.close()
            self.assertEqual(store.history("citizen-old", "CC-OLD-001")["request"]["title"], "Existing request")


if __name__ == "__main__":
    unittest.main()
