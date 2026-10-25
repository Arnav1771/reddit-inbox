"""
Unit tests for RedditFeedCrawler XML parsing and HTML sanitization.
"""

import unittest
from src.feed_crawler import RedditFeedCrawler

SAMPLE_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>r/BestGitHubRepos</title>
  <entry>
    <title>Awesome Tool: REA Reverse Engineering MCP</title>
    <link href="https://www.reddit.com/r/BestGitHubRepos/comments/12345/awesome_tool/"/>
    <author><name>test_author</name></author>
    <updated>2026-10-25T12:00:00+00:00</updated>
    <content type="html">&lt;p&gt;Check out &lt;a href="https://github.com/morluto/rea"&gt;morluto/rea&lt;/a&gt; for decompilation.&lt;/p&gt;</content>
    <id>t3_12345</id>
  </entry>
</feed>
"""


class TestFeedCrawler(unittest.TestCase):

    def setUp(self):
        self.crawler = RedditFeedCrawler()

    def test_parse_atom_xml(self):
        posts = self.crawler.parse_atom_xml(SAMPLE_ATOM_XML, "BestGitHubRepos")
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post["title"], "Awesome Tool: REA Reverse Engineering MCP")
        self.assertEqual(post["author"], "test_author")
        self.assertIn("https://github.com/morluto/rea", post["content"])
        self.assertEqual(post["subreddit"], "r/BestGitHubRepos")

    def test_strip_html(self):
        raw = '<p>Hello &amp; welcome &lt;world&gt;! <a href="https://github.com/test/repo">Link</a></p>'
        cleaned = self.crawler._strip_html(raw)
        self.assertIn("Hello & welcome <world>!", cleaned)
        self.assertIn("https://github.com/test/repo", cleaned)


if __name__ == "__main__":
    unittest.main()
