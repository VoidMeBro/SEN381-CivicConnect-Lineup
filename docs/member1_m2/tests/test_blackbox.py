"""Black-box validation and partition checks at public service boundaries."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "product"))
from lifecycle import InvalidTransition, SqliteLifecycleStore

TEST_TMP = Path(__file__).resolve().parents[1] / ".test-tmp"
TEST_TMP.mkdir(exist_ok=True)


class BlackBoxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TMP)
        self.addCleanup(self.temp.cleanup)
        self.store = SqliteLifecycleStore(Path(self.temp.name) / "blackbox.sqlite3")
        self.store.initialise()
        self.store.register_citizen("citizen", "CitizenPass-381!", "2026-10-01T10:00:00+00:00")
        self.store.bootstrap_administrator("admin", "AdminPass-381!", "2026-10-01T10:00:00+00:00")

    def test_FR07_title_below_minimum_is_rejected(self):
        with self.assertRaises(InvalidTransition):
            self.store.submit_request("citizen", "abcd", "A valid description for request.", "Park Road", "water", "2026-10-01T10:00:00+00:00")

    def test_FR07_title_at_minimum_is_accepted(self):
        reference = self.store.submit_request("citizen", "12345", "A valid description for request.", "Park Road", "water", "2026-10-01T10:00:00+00:00")
        self.assertTrue(reference.startswith("CC-20261001-"))

    def test_FR07_description_above_maximum_is_rejected(self):
        with self.assertRaises(InvalidTransition):
            self.store.submit_request("citizen", "Valid title", "x" * 2001, "Park Road", "water", "2026-10-01T10:00:00+00:00")

    def test_FR07_location_below_minimum_is_rejected(self):
        with self.assertRaises(InvalidTransition):
            self.store.submit_request("citizen", "Valid title", "A valid description for request.", "AB", "water", "2026-10-01T10:00:00+00:00")

    def test_FR07_inactive_category_is_rejected(self):
        self.store.manage_category("admin", "water", "Water", "Water", "0")
        with self.assertRaises(InvalidTransition):
            self.store.submit_request("citizen", "Valid title", "A valid description for request.", "Park Road", "water", "2026-10-01T10:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
