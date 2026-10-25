"""
reddit-inbox configuration
Defines tracked subreddits, scoring thresholds, cache paths, and networking headers.
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VAULT_DIR = BASE_DIR / "vault"
WEB_DIR = BASE_DIR / "web"

# Cache and data files
INBOX_FILE = DATA_DIR / "inbox.json"
CACHE_FILE = DATA_DIR / "cache.json"
LOW_CONFIDENCE_FILE = DATA_DIR / "quarantine.json"
WEB_DATA_FILE = WEB_DIR / "data.json"

# Signal & Confidence Thresholds
DEFAULT_WORTHY_THRESHOLD = 80.0  # Only items >= 80% make it to the main feed/vault
MIN_DISPLAY_THRESHOLD = 60.0

# Subreddits monitored by default
DEFAULT_SUBREDDITS = [
    {
        "name": "ClaudeCode",
        "category": "Agentic Architecture",
        "description": "Claude Code CLI, subagent harnesses, hooks, SKILL.md, and terminal workflows",
        "weight": 1.15
    },
    {
        "name": "ClaudeAI",
        "category": "LLM Paradigms",
        "description": "Extended thinking, prompt caching TTL, structured outputs, and frontier capabilities",
        "weight": 1.05
    },
    {
        "name": "BestGitHubRepos",
        "category": "Open Source Breakthroughs",
        "description": "Curated, high-impact GitHub repositories and developer tools",
        "weight": 1.20
    },
    {
        "name": "UI_Design",
        "category": "UI/UX & Anti-Slop",
        "description": "Design systems, typography, micro-interactions, and human-crafted interfaces",
        "weight": 1.10
    },
    {
        "name": "web_design",
        "category": "UI/UX & Anti-Slop",
        "description": "Frontend craft, responsive design patterns, and rejecting AI slop",
        "weight": 1.05
    },
    {
        "name": "Frontend",
        "category": "Web Engineering",
        "description": "Modern web stacks, performance optimization, and layout architectures",
        "weight": 1.00
    },
    {
        "name": "LocalLLaMA",
        "category": "Local AI & Weights",
        "description": "Local inference, quantization, open weights, and on-premise AI engineering",
        "weight": 1.10
    },
    {
        "name": "projects",
        "category": "Indie Engineering",
        "description": "Real software builds, full-stack prototypes, and independent developer releases",
        "weight": 1.00
    }
]

# Network settings
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RedditInboxEngine/1.0.0 (by /u/Arnav1771; high-signal SDE curator)"
SALAMANCE_PROXY_URL = "http://130.210.17.89:5050"
REQUEST_TIMEOUT = 12.0
