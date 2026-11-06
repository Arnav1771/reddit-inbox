"""
cli.py
Command-line interface for reddit-inbox.
Supports init, doctor, sync, eval, serve, add-sub, and stats commands.
"""

import argparse
import sys
import os
import io
import json
import http.server
import socketserver
import urllib.request
from pathlib import Path
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.config import (
    DEFAULT_SUBREDDITS, DEFAULT_WORTHY_THRESHOLD, DATA_DIR, VAULT_DIR,
    WEB_DIR, WEB_DATA_FILE, USER_AGENT, SALAMANCE_PROXY_URL
)
from src.classifier import RedditClassifier
from src.feed_crawler import RedditFeedCrawler
from src.vault import VaultManager
from src.seeds import INITIAL_HIGH_SIGNAL_SEEDS


def cmd_init(args):
    """Initializes repository folders and seeds baseline curated high-signal intelligence."""
    print("🚀 Initializing reddit-inbox engine...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    WEB_DIR.mkdir(parents=True, exist_ok=True)

    classifier = RedditClassifier(worthy_threshold=DEFAULT_WORTHY_THRESHOLD)
    vault = VaultManager(VAULT_DIR)

    worthy = []
    noise = []
    print(f"📦 Evaluating {len(INITIAL_HIGH_SIGNAL_SEEDS)} baseline seeds with 'Learn, Understand, Worthy' engine...")
    for seed in INITIAL_HIGH_SIGNAL_SEEDS:
        res = classifier.evaluate(seed, sub_weight=1.1)
        if res["is_worthy"]:
            worthy.append(res)
        else:
            noise.append(res)

    stats = vault.save_sync_results(worthy, noise)
    print(f"✅ Initialization complete!")
    print(f"   • High-Signal Worthy Posts: {stats['total_worthy']} (Threshold: ≥{DEFAULT_WORTHY_THRESHOLD}%)")
    print(f"   • Vault generated at: {VAULT_DIR}")
    print(f"   • Web data generated at: {WEB_DATA_FILE}")
    print("\nNext step: run 'python -m src.cli doctor' or 'python -m src.cli serve' to view dashboard.")


def cmd_doctor(args):
    """Diagnostics and connectivity health check."""
    print("🩺 Running reddit-inbox diagnostics...")
    print(f"Python Version: {sys.version.split()[0]} (Standard Library only - zero pip bloat)")
    
    # Check Directories
    dirs = [("Data Dir", DATA_DIR), ("Vault Dir", VAULT_DIR), ("Web Dir", WEB_DIR)]
    for name, path in dirs:
        exists = path.exists()
        print(f"  [{'✓' if exists else '✗'}] {name}: {path} ({'Ready' if exists else 'Missing'})")

    # Check Reddit Connectivity
    print("\n🌐 Testing Network Connectivity:")
    test_url = "https://www.reddit.com/r/BestGitHubRepos/.rss?limit=1"
    try:
        req = urllib.request.Request(test_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            print(f"  [✓] Direct Reddit RSS: HTTP {resp.status} OK")
    except Exception as e:
        print(f"  [!] Direct Reddit RSS: {e} (Will use proxy fallback)")

    # Check Salamance Proxy Relay
    try:
        proxy_req = urllib.request.Request(
            f"{SALAMANCE_PROXY_URL}/api/status",
            headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(proxy_req, timeout=5.0) as resp:
            print(f"  [✓] Salamance Oracle VM Relay ({SALAMANCE_PROXY_URL}): HTTP {resp.status} OK")
    except Exception:
        print(f"  [i] Salamance Relay ({SALAMANCE_PROXY_URL}): Standby / Optional")

    print("\n🎯 Diagnostic check complete.")


def cmd_sync(args):
    """Synchronizes live feeds from monitored subreddits, applies confidence scoring, and updates vault."""
    threshold = args.threshold or DEFAULT_WORTHY_THRESHOLD
    limit = args.limit or 15

    print(f"🔄 Starting reddit-inbox sync across {len(DEFAULT_SUBREDDITS)} subreddits...")
    print(f"   Confidence Filter: ≥{threshold}% (Low-signal noise will be quarantined)")

    crawler = RedditFeedCrawler()
    classifier = RedditClassifier(worthy_threshold=threshold)
    vault = VaultManager(VAULT_DIR)

    all_worthy = []
    all_noise = []

    for sub_info in DEFAULT_SUBREDDITS:
        sub_name = sub_info["name"]
        category = sub_info.get("category", "Tech")
        weight = sub_info.get("weight", 1.0)

        print(f"  ⏳ Polling r/{sub_name} (limit={limit})...", end="", flush=True)
        xml_data = crawler.fetch_subreddit_atom(sub_name, limit=limit)
        if not xml_data:
            print(" [Offline/Throttled - using cached/seeded posts]")
            continue

        posts = crawler.parse_atom_xml(xml_data, sub_name)
        print(f" Found {len(posts)} posts -> Evaluating: ", end="", flush=True)

        worthy_count = 0
        for p in posts:
            p["category"] = category
            evaluated = classifier.evaluate(p, sub_weight=weight)
            if evaluated["is_worthy"]:
                all_worthy.append(evaluated)
                worthy_count += 1
            else:
                all_noise.append(evaluated)

        print(f"{worthy_count} worthy / {len(posts) - worthy_count} noise")

    # If no live posts returned due to network limits, ensure pre-seeded baseline is present
    if not all_worthy and not vault.load_inbox():
        print("  ℹ️ Injecting initial verified baseline posts...")
        for seed in INITIAL_HIGH_SIGNAL_SEEDS:
            ev = classifier.evaluate(seed, sub_weight=1.1)
            if ev["is_worthy"]:
                all_worthy.append(ev)

    stats = vault.save_sync_results(all_worthy, all_noise)
    print("\n" + "=" * 60)
    print("📊 SYNC SUMMARY")
    print(f"   • High-Signal Worthy Items Promoted: {stats['new_worthy_added']} new ({stats['total_worthy']} total)")
    print(f"   • Quarantined Noise Filtered Out: {stats['quarantined_noise']}")
    print(f"   • Overall Signal Ratio: {stats['signal_ratio']}%")
    print(f"   • Updated Markdown Vault: {VAULT_DIR / 'RADAR.md'}")
    print("=" * 60)


def cmd_eval(args):
    """Evaluates an ad-hoc post or text snippet and outputs its confidence scoring breakdown."""
    text = args.text
    title = args.title or "Interactive Evaluation Target"
    if not text:
        print("Error: --text is required for evaluation.")
        sys.exit(1)

    classifier = RedditClassifier(worthy_threshold=DEFAULT_WORTHY_THRESHOLD)
    post = {
        "title": title,
        "content": text,
        "url": args.url or "https://reddit.com/r/eval_test",
        "author": "tester",
        "published_at": "Now",
        "subreddit": args.subreddit or "r/Custom"
    }

    result = classifier.evaluate(post)
    print("\n" + "=" * 60)
    print(f"🎯 EVALUATION BREAKDOWN: {result['verdict']}")
    print(f"Confidence Score: {result['confidence_score']}% (Threshold: ≥{DEFAULT_WORTHY_THRESHOLD}%)")
    print("=" * 60)
    print("\nFactors Applied:")
    for f in result["factors"]:
        print(f"  • [{f['delta']}] {f['name']}: {f['detail']}")

    print("\nExtracted GitHub Repositories:")
    if result["github_repos"]:
        for repo in result["github_repos"]:
            print(f"  • {repo}")
    else:
        print("  • None detected")

    print("\nSynthesized 2-3 Line Brief:")
    for line in result["synthesis"]:
        print(f"  {line}")
    print("=" * 60)


def cmd_serve(args):
    """Serves the Google Stitch / Notion interactive dashboard locally."""
    port = args.port or 8085
    docs_dir = Path(__file__).resolve().parent.parent / "docs"
    web_dir = Path(__file__).resolve().parent.parent / "web"
    target_dir = docs_dir if docs_dir.exists() else web_dir
    
    # Ensure web data exists
    if not (target_dir / "data.json").exists():
        print("Web data not found. Running initial seed...")
        cmd_init(args)

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args_inner, **kwargs):
            super().__init__(*args_inner, directory=str(target_dir), **kwargs)

        def log_message(self, format, *args_inner):
            # Suppress noisy HTTP asset logs
            pass

    print("\n" + "=" * 60)
    print(f"⚡ Reddit Inbox Dashboard running at: http://localhost:{port}")
    print("   Notion / Google Stitch Dark Specification · Live Confidence Slider")
    print("   Press Ctrl+C to terminate server.")
    print("=" * 60)

    with socketserver.TCPServer(("0.0.0.0", port), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


def cmd_stats(args):
    """Displays signal-to-noise analytics and discovered repositories."""
    vault = VaultManager(VAULT_DIR)
    inbox = vault.load_inbox()

    print("\n" + "=" * 60)
    print("📈 REDDIT INBOX INTELLIGENCE STATS")
    print("=" * 60)
    print(f"Total High-Signal Items: {len(inbox)}")
    
    # Group by Subreddit
    sub_counts = {}
    repos = set()
    for item in inbox:
        sub = item.get("subreddit", "Other")
        sub_counts[sub] = sub_counts.get(sub, 0) + 1
        for r in item.get("github_repos", []):
            repos.add(r)

    print("\nBreakdown by Subreddit:")
    for sub, count in sorted(sub_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {sub:22}: {count} curated posts")

    print(f"\nDiscovered GitHub Repositories ({len(repos)} total):")
    for r in sorted(repos):
        print(f"  • {r}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Reddit Inbox - High-Signal SDE Intelligence Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize folders and seed baseline intelligence")
    p_init.set_defaults(func=cmd_init)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Run diagnostics and network health checks")
    p_doctor.set_defaults(func=cmd_doctor)

    # sync
    p_sync = subparsers.add_parser("sync", help="Synchronize subreddits and apply confidence scoring")
    p_sync.add_argument("--threshold", type=float, default=DEFAULT_WORTHY_THRESHOLD, help="Minimum confidence threshold (default: 80.0)")
    p_sync.add_argument("--limit", type=int, default=15, help="Number of posts per subreddit")
    p_sync.set_defaults(func=cmd_sync)

    # eval
    p_eval = subparsers.add_parser("eval", help="Evaluate an ad-hoc post or text snippet")
    p_eval.add_argument("--text", type=str, required=True, help="Post content or body text")
    p_eval.add_argument("--title", type=str, default="", help="Post title")
    p_eval.add_argument("--url", type=str, default="", help="Post URL")
    p_eval.add_argument("--subreddit", type=str, default="r/ManualTest", help="Subreddit name")
    p_eval.set_defaults(func=cmd_eval)

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch local Google Stitch web dashboard")
    p_serve.add_argument("--port", type=int, default=8085, help="Port to listen on (default: 8085)")
    p_serve.set_defaults(func=cmd_serve)

    # stats
    p_stats = subparsers.add_parser("stats", help="Show intelligence metrics and discovered repos")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
