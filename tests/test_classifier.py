"""
Unit tests for RedditClassifier scoring and noise filtering.
"""

import unittest
from src.classifier import RedditClassifier


class TestRedditClassifier(unittest.TestCase):

    def setUp(self):
        self.classifier = RedditClassifier(worthy_threshold=80.0)

    def test_high_signal_oss_post_is_worthy(self):
        post = {
            "title": "Announcing fast-mcp: Zero-overhead Model Context Protocol server in Rust",
            "content": (
                "We built an ultra-lean MCP server using Rust and SQLite. "
                "It integrates with Claude Code CLI and solves token context bloat using progressive disclosure. "
                "Tested with Playwright E2E and runs in under 4MB RAM. "
                "Repository: https://github.com/developer/fast-mcp\n\n"
                "```rust\nfn handle_mcp_call() -> Result<(), Error> {}\n```"
            ),
            "url": "https://reddit.com/r/BestGitHubRepos/test1",
            "published_at": "2026-10-25T10:00:00Z",
            "subreddit": "r/BestGitHubRepos"
        }
        res = self.classifier.evaluate(post, sub_weight=1.1)
        self.assertTrue(res["is_worthy"])
        self.assertGreaterEqual(res["confidence_score"], 80.0)
        self.assertEqual(res["verdict"], "WORTHY")
        self.assertIn("https://github.com/developer/fast-mcp", res["github_repos"])
        self.assertEqual(len(res["synthesis"]), 3)

    def test_complaint_and_billing_is_rejected_as_noise(self):
        post = {
            "title": "Is Claude down? My account was banned and I was charged twice for subscription!",
            "content": "Claude is down again today. I opened a billing support ticket for refund.",
            "url": "https://reddit.com/r/ClaudeAI/test_complaint",
            "published_at": "2026-10-25T10:00:00Z",
            "subreddit": "r/ClaudeAI"
        }
        res = self.classifier.evaluate(post, sub_weight=1.0)
        self.assertFalse(res["is_worthy"])
        self.assertLess(res["confidence_score"], 50.0)
        self.assertEqual(res["verdict"], "FILTERED_NOISE")

    def test_low_effort_get_rich_quick_is_rejected(self):
        post = {
            "title": "Make $5000 passive income with this simple wrapper for gpt!",
            "content": "Check out my wrapper to 10x your money with dropshipping prompts.",
            "url": "https://reddit.com/r/projects/test_spam",
            "published_at": "2026-10-25T10:00:00Z",
            "subreddit": "r/projects"
        }
        res = self.classifier.evaluate(post, sub_weight=1.0)
        self.assertFalse(res["is_worthy"])
        self.assertLess(res["confidence_score"], 40.0)

    def test_github_repo_extraction(self):
        text = "Check out https://github.com/anthropics/skills and https://github.com/morluto/rea.git for details."
        repos = self.classifier.extract_github_repos(text)
        self.assertEqual(len(repos), 2)
        self.assertIn("https://github.com/anthropics/skills", repos)
        self.assertIn("https://github.com/morluto/rea", repos)


if __name__ == "__main__":
    unittest.main()
