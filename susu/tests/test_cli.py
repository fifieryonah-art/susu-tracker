"""Exercise the CLI in separate processes against temporary state files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from susu.errors import StateFileError
from susu.storage import load, save


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "group.json"

    def run_cli(self, *args, expected=0):
        result = subprocess.run(
            [sys.executable, "-m", "susu", "--file", str(self.path), *args],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def create_members(self):
        self.run_cli("create", "50")
        for name in ("Ama", "Kofi", "Esi"):
            self.run_cli("add", name)

    def test_persistent_partial_payment_and_payout(self):
        self.create_members()
        for name, amount in (("Ama", "50"), ("Kofi", "50"), ("Esi", "30")):
            self.run_cli("pay", name, "1", amount)
        before = self.path.read_bytes()
        self.assertIn("Esi owes 20.00", self.run_cli("close", expected=1).stdout)
        self.assertEqual(self.path.read_bytes(), before)
        self.run_cli("pay", "Esi", "1", "20")
        self.assertIn("Ama receives 150.00", self.run_cli("close").stdout)
        report = json.loads(self.run_cli("report").stdout)
        self.assertEqual(report["current_week"], 2)
        self.assertEqual(report["next_recipient"], "Kofi")
        self.assertEqual(report["payout_history"],
                         [{"week": 1, "member": "Ama", "amount": "150.00"}])

    def test_rejected_actions_preserve_file(self):
        self.create_members()
        before = self.path.read_bytes()
        for command in (("create", "20"), ("add", "Ama"),
                        ("pay", "Yaw", "1", "50"), ("pay", "Ama", "1", "51"),
                        ("pay", "Ama", "2", "50"), ("pay", "Ama", "1", "0")):
            with self.subTest(command=command):
                self.run_cli(*command, expected=1)
                self.assertEqual(self.path.read_bytes(), before)

    def test_missing_and_malformed_file_errors(self):
        self.assertIn("Cannot read", self.run_cli("report", expected=1).stderr)
        self.path.write_text("not json", encoding="utf-8")
        before = self.path.read_bytes()
        self.run_cli("add", "Ama", expected=1)
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_saved_events_are_rejected(self):
        documents = [[], {"version": 2, "weekly_contribution": "50", "events": []},
                     {"version": 1, "weekly_contribution": "50", "events": [
                         {"action": "add", "member": "Ama"}, {"action": "close"}]},
                     {"version": 1, "weekly_contribution": "50", "events": [
                         {"action": "unknown"}]}]
        for document in documents:
            with self.subTest(document=document):
                self.path.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(StateFileError):
                    load(self.path)

    def test_failed_replace_preserves_saved_state(self):
        self.create_members()
        before = self.path.read_bytes()
        _, document = load(self.path)
        document["events"].append({"action": "pay", "member": "Ama", "week": 1, "amount": "20"})
        with patch("susu.storage.os.replace", side_effect=OSError("write failure")):
            with self.assertRaises(StateFileError):
                save(self.path, document)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


if __name__ == "__main__":
    unittest.main()
