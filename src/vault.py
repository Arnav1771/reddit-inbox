"""
vault.py
Vault builder and state persistence for Reddit Inbox.
Generates structured Markdown knowledge vaults and web dashboard JSON.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from src.config import INBOX_FILE, LOW_CONFIDENCE_FILE, VAULT_DIR, WEB_DATA_FILE, DOCS_DATA_FILE


class VaultManager:
    """Manages persistent storage, Markdown knowledge base, and web dashboard data."""

    def __init__(
        self,
        vault_dir: Path = VAULT_DIR,
        inbox_file: Path = INBOX_FILE,
        quarantine_file: Path = LOW_CONFIDENCE_FILE,
        web_data_file: Path = WEB_DATA_FILE
    ):
        self.vault_dir = vault_dir
        self.inbox_file = inbox_file
        self.quarantine_file = quarantine_file
        self.web_data_file = web_data_file
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_file.parent.mkdir(parents=True, exist_ok=True)

    def load_inbox(self) -> List[Dict[str, Any]]:
        """Loads previously saved worthy items."""
        if self.inbox_file.exists():
            try:
                with open(self.inbox_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_sync_results(self, worthy_items: List[Dict[str, Any]], noise_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merges new items with existing inbox, saves to disk, and updates Markdown/web exports.
        """
        existing_inbox = self.load_inbox()
        existing_urls = {item["url"] for item in existing_inbox if "url" in item}

        new_worthy = []
        for item in worthy_items:
            if item.get("url") not in existing_urls:
                existing_urls.add(item.get("url"))
                new_worthy.append(item)

        # Prepend new worthy items (most recent first)
        combined_inbox = new_worthy + existing_inbox

        # Save worthy items
        with open(self.inbox_file, "w", encoding="utf-8") as f:
            json.dump(combined_inbox, f, indent=2, ensure_ascii=False)

        # Save quarantined noise items
        with open(self.quarantine_file, "w", encoding="utf-8") as f:
            json.dump(noise_items[:100], f, indent=2, ensure_ascii=False)

        # Generate Markdown Vault files
        self._write_radar_markdown(combined_inbox)
        self._write_repositories_markdown(combined_inbox)
        self._write_design_systems_markdown(combined_inbox)

        # Generate Web JSON
        stats = {
            "total_worthy": len(combined_inbox),
            "new_worthy_added": len(new_worthy),
            "quarantined_noise": len(noise_items),
            "signal_ratio": round((len(combined_inbox) / max(1, len(combined_inbox) + len(noise_items))) * 100, 1),
            "last_synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        web_payload = {
            "metadata": stats,
            "posts": combined_inbox,
            "quarantine_sample": noise_items[:15]
        }
        with open(self.web_data_file, "w", encoding="utf-8") as f:
            json.dump(web_payload, f, indent=2, ensure_ascii=False)

        # Write data.js for zero-CORS file:// local double-click execution
        js_content = f"window.__REDDIT_INBOX_DATA__ = {json.dumps(web_payload, indent=2, ensure_ascii=False)};\n"
        with open(self.web_data_file.parent / "data.js", "w", encoding="utf-8") as f:
            f.write(js_content)

        if DOCS_DATA_FILE.parent.exists():
            with open(DOCS_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(web_payload, f, indent=2, ensure_ascii=False)
            with open(DOCS_DATA_FILE.parent / "data.js", "w", encoding="utf-8") as f:
                f.write(js_content)

        return stats

    def _write_radar_markdown(self, items: List[Dict[str, Any]]):
        """Generates vault/RADAR.md with executive technical briefs."""
        file_path = self.vault_dir / "RADAR.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# 📡 High-Signal Reddit Engineering Radar\n\n")
            f.write("> **Strictly Curated Intelligence** · Filtered at ≥80.0% Confidence Threshold\n\n")
            f.write(f"*Last Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n\n")
            f.write("---\n\n")

            if not items:
                f.write("*No high-signal posts collected yet. Run `python -m src.cli sync`.* \n")
                return

            for item in items:
                confidence = item.get("confidence_score", 0.0)
                sub = item.get("subreddit", "")
                date_str = item.get("published_at", "")[:10] or "Recent"
                title = item.get("title", "Untitled")
                url = item.get("url", "#")
                repos = item.get("github_repos", [])
                synthesis = item.get("synthesis", [])

                f.write(f"### [{title}]({url})\n\n")
                f.write(f"**Subreddit:** `{sub}` | **Date:** `{date_str}` | **Confidence:** `{confidence}%` 🛡️\n\n")

                if repos:
                    repo_links = ", ".join([f"[{r.replace('https://github.com/', '')}]({r})" for r in repos])
                    f.write(f"**Discovered GitHub Repositories:** {repo_links}\n\n")

                f.write("**High-Signal Brief:**\n")
                for line in synthesis:
                    f.write(f"- {line}\n")

                f.write("\n<details><summary>Scoring Factors</summary>\n\n")
                for factor in item.get("factors", []):
                    f.write(f"- `{factor.get('delta', '')}`: {factor.get('name', '')} ({factor.get('detail', '')})\n")
                f.write("\n</details>\n\n---\n\n")

    def _write_repositories_markdown(self, items: List[Dict[str, Any]]):
        """Generates vault/REPOSITORIES.md indexing all discovered GitHub links."""
        file_path = self.vault_dir / "REPOSITORIES.md"
        repos_map = {}
        for item in items:
            for repo in item.get("github_repos", []):
                if repo not in repos_map:
                    repos_map[repo] = {
                        "repo": repo,
                        "title": item.get("title"),
                        "subreddit": item.get("subreddit"),
                        "date": item.get("published_at", "")[:10],
                        "source_url": item.get("url")
                    }

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# 📦 Discovered Open Source Repositories\n\n")
            f.write("> **Verified Developer Tools & Libraries Discovered from High-Confidence Discussions**\n\n")
            f.write("---\n\n")

            if not repos_map:
                f.write("*No repositories discovered yet.*\n")
                return

            f.write("| Repository | Subreddit | Context & Origin | Discovered |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for repo, data in sorted(repos_map.items()):
                short_name = repo.replace("https://github.com/", "")
                title_clean = (data['title'][:55] + "...") if len(data['title']) > 55 else data['title']
                f.write(f"| [{short_name}]({repo}) | `{data['subreddit']}` | [{title_clean}]({data['source_url']}) | `{data['date']}` |\n")

    def _write_design_systems_markdown(self, items: List[Dict[str, Any]]):
        """Generates vault/DESIGN_SYSTEMS.md for UI/UX insights."""
        file_path = self.vault_dir / "DESIGN_SYSTEMS.md"
        design_items = [
            item for item in items 
            if item.get("subreddit") in {"r/UI_Design", "r/web_design", "r/Frontend"} or
            any(k in " ".join(item.get("matched_keywords", [])) for k in ["design", "typography", "anti-slop", "contrast"])
        ]

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# 🎨 UI/UX & Anti-Slop Design Systems\n\n")
            f.write("> **Curated Design Paradigms, Micro-interactions, and Production UI Architectures**\n\n")
            f.write("---\n\n")

            if not design_items:
                f.write("*No design items filtered yet.*\n")
                return

            for item in design_items:
                f.write(f"### [{item.get('title')}]({item.get('url')})\n\n")
                f.write(f"**Origin:** `{item.get('subreddit')}` | **Confidence:** `{item.get('confidence_score')}%`\n\n")
                for line in item.get("synthesis", []):
                    f.write(f"- {line}\n")
                f.write("\n---\n\n")
