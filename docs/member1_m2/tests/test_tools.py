"""Static checks that guard the traceable CI quality boundary."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ToolingTests(unittest.TestCase):
    def test_ci_compiles_tests_and_runs_all_required_check_categories(self):
        workflow = (ROOT.parent.parent / ".github" / "workflows" / "quality.yml").read_text(encoding="utf-8")
        for required in ("compileall", "unittest discover", "performance_smoke.py", "bandit", "gitleaks"):
            with self.subTest(required=required):
                self.assertIn(required, workflow)

    def test_current_sources_contain_no_committed_database_or_private_key(self):
        forbidden_suffixes = {".sqlite3", ".db", ".pem", ".key"}
        files = [path for path in ROOT.parent.parent.rglob("*") if path.is_file() and ".git" not in path.parts and ".test-tmp" not in path.parts and "data" not in path.parts]
        offenders = [path for path in files if path.suffix.lower() in forbidden_suffixes]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
