"""
Unit tests for VaultManager file generation and state merging.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from src.vault import VaultManager


class TestVaultManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.inbox_file = self.test_dir / "inbox.json"
        self.quarantine_file = self.test_dir / "quarantine.json"
        self.web_data_file = self.test_dir / "data.json"
        self.vault = VaultManager(
            vault_dir=self.test_dir,
            inbox_file=self.inbox_file,
            quarantine_file=self.quarantine_file,
            web_data_file=self.web_data_file
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_sync_results_creates_markdown(self):
        worthy = [{
            "title": "High Signal Architecture",
            "url": "https://reddit.com/r/ClaudeCode/post1",
            "author": "dev",
            "published_at": "2026-10-25T10:00:00Z",
            "subreddit": "r/ClaudeCode",
            "confidence_score": 92.5,
            "is_worthy": True,
            "verdict": "WORTHY",
            "github_repos": ["https://github.com/test/project"],
            "synthesis": ["Line 1", "Line 2", "Line 3"],
            "factors": [{"name": "Repo", "delta": "+25", "detail": "Test"}]
        }]
        noise = [{
            "title": "Service Outage",
            "url": "https://reddit.com/r/ClaudeAI/outage",
            "confidence_score": 25.0,
            "is_worthy": False
        }]

        stats = self.vault.save_sync_results(worthy, noise)
        self.assertEqual(stats["total_worthy"], 1)
        self.assertEqual(stats["quarantined_noise"], 1)

        radar_file = self.test_dir / "RADAR.md"
        self.assertTrue(radar_file.exists())
        content = radar_file.read_text(encoding="utf-8")
        self.assertIn("High Signal Architecture", content)
        self.assertIn("92.5%", content)


if __name__ == "__main__":
    unittest.main()
