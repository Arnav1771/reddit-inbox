"""
feed_crawler.py
Resilient RSS/Atom feed reader for Reddit.
Parses Atom feeds, handles Reddit User-Agent standards, and falls back to Salamance proxy if throttled.
"""

import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import re
import html
from typing import List, Dict, Any, Optional

from src.config import USER_AGENT, REQUEST_TIMEOUT, SALAMANCE_PROXY_URL


class RedditFeedCrawler:
    """Fetches and parses Atom/RSS feeds from Reddit subreddits."""

    def __init__(self, user_agent: str = USER_AGENT):
        self.user_agent = user_agent

    def fetch_subreddit_atom(self, subreddit: str, limit: int = 25) -> Optional[str]:
        """
        Fetches the raw Atom XML for a given subreddit.
        Attempts direct request first; falls back to Salamance gateway if rate-limited.
        """
        url = f"https://www.reddit.com/r/{subreddit}/.rss?limit={limit}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/atom+xml,application/xml,text/xml",
                "Cache-Control": "max-age=180"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 403):
                return self._fetch_via_proxy(url)
            return None
        except Exception:
            return self._fetch_via_proxy(url)

    def _fetch_via_proxy(self, target_url: str) -> Optional[str]:
        """Attempts fetching target URL through Salamance Oracle VM proxy gateway."""
        try:
            proxy_endpoint = f"{SALAMANCE_PROXY_URL}/api/proxy?url={urllib.parse.quote(target_url)}"
            req = urllib.request.Request(
                proxy_endpoint,
                headers={"User-Agent": self.user_agent}
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return None

    def _get_elem(self, parent: ET.Element, tag: str, ns: Dict[str, str]) -> Optional[ET.Element]:
        """Safely locates child element across namespace variations without boolean truthiness pitfalls."""
        elem = parent.find(f"atom:{tag}", ns)
        if elem is not None:
            return elem
        return parent.find(tag)

    def parse_atom_xml(self, xml_content: str, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Parses Reddit Atom XML into structured post objects.
        """
        posts = []
        if not xml_content or not xml_content.strip():
            return posts

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return posts

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if not entries:
            entries = root.findall("entry")

        for entry in entries:
            title_elem = self._get_elem(entry, "title", ns)
            title = title_elem.text.strip() if (title_elem is not None and title_elem.text) else ""

            # Link
            url = ""
            link_elem = self._get_elem(entry, "link", ns)
            if link_elem is not None:
                url = link_elem.attrib.get("href", "")

            # Author
            author_elem = entry.find("atom:author/atom:name", ns)
            if author_elem is None:
                author_elem = entry.find("author/name")
            author = author_elem.text.strip() if (author_elem is not None and author_elem.text) else "unknown"

            # Published / Updated date
            updated_elem = self._get_elem(entry, "updated", ns)
            if updated_elem is None:
                updated_elem = self._get_elem(entry, "published", ns)
            published_at = updated_elem.text.strip() if (updated_elem is not None and updated_elem.text) else ""

            # Content
            content_elem = self._get_elem(entry, "content", ns)
            raw_content = content_elem.text.strip() if (content_elem is not None and content_elem.text) else ""
            
            clean_content = self._strip_html(raw_content)

            id_elem = self._get_elem(entry, "id", ns)
            post_id = id_elem.text.strip() if (id_elem is not None and id_elem.text) else url

            posts.append({
                "id": post_id,
                "title": title,
                "url": url,
                "author": author,
                "published_at": published_at,
                "content": clean_content,
                "raw_html": raw_content,
                "subreddit": f"r/{subreddit_name}"
            })

        return posts

    def _strip_html(self, raw_html: str) -> str:
        """Removes HTML tags and unescapes entities into readable plain text."""
        if not raw_html:
            return ""
        # Convert hyperlinks before stripping tags: <a href="url">text</a> -> text (url)
        text = re.sub(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>', r'\2 (\1)', raw_html)
        # Strip all HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Unescape HTML entities after tag removal so encoded brackets &lt; &gt; are preserved
        text = html.unescape(text)
        # Consolidate whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()
