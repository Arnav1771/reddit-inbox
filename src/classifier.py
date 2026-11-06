"""
classifier.py
The 'Learn, Understand, Worthy' Intelligence Engine for Reddit Inbox.
Evaluates technical merit, detects noise/complaints/slop, computes a 0-100% confidence score,
and synthesizes a crisp 2-3 line engineering brief.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# Regex to detect GitHub repository URLs
GITHUB_REPO_REGEX = re.compile(
    r"https?://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)(?:/(?:tree|blob)/[^\s\)\"\'>]*)?",
    re.IGNORECASE
)

# High-Signal Technical Anchor Keywords
TECH_KEYWORDS = {
    # Agentic & LLM Architecture
    "mcp": 3.0, "model context protocol": 3.5, "worktree": 3.0, "git worktree": 3.5,
    "prompt cache": 3.0, "cache ttl": 3.0, "structured output": 2.5, "extended thinking": 3.0,
    "subagent": 2.5, "harness": 2.5, "skill.md": 3.5, "progressive disclosure": 3.0,
    "lifecycle hook": 2.5, "claude code": 3.0, "tokenizer": 2.0, "token budget": 2.5,
    "context window": 2.0, "system prompt": 2.0, "clean-room": 3.0,

    # Systems & Engineering
    "reverse engineer": 3.0, "decompil": 2.5, "ghidra": 3.0, "asar": 2.5,
    "webrtc": 3.0, "sqlite": 2.0, "rust": 2.5, "playwright": 2.5, "e2e": 2.0,
    "daemon": 2.0, "ipc": 2.5, "websocket": 2.0, "docker": 1.5, "zero-dependency": 2.5,

    # Modern UI/UX & Anti-Slop
    "design token": 3.0, "anti-slop": 3.5, "micro-interaction": 2.5, "typography": 2.0,
    "contrast ratio": 2.5, "spring physics": 3.0, "motion design": 2.0, "wcag": 2.5,
    "component system": 2.0, "responsive grid": 2.0, "layout shift": 2.0, "figma": 1.5,
}

# Low-Signal & Complaint Patterns (Severe Penalties)
NOISE_PATTERNS = [
    (r"\b(is down|outage|status page|server down)\b", 40.0, "Outage/Service Status Complaint"),
    (r"\b(billing|charged twice|refund|subscription cancelled|credit card)\b", 35.0, "Billing & Payment Grievance"),
    (r"\b(banned|account suspended|appealed my ban)\b", 35.0, "Account Ban Grievance"),
    (r"\b(why does anthropic hate|openai is evil|claude is getting dumber)\b", 30.0, "Subjective Venting"),
    (r"\b(make \$?\d+[\w\s]*with ai|passive income|dropshipping|easy money)\b", 45.0, "Get-Rich-Quick / Fluff Spam"),
    (r"\b(simple wrapper for (gpt|claude|openai)|check out my wrapper)\b", 30.0, "Trivial AI Wrapper"),
    (r"\b(should i learn python or|is coding dead|will ai replace us)\b", 25.0, "Generic Speculative Fluff"),
]


class RedditClassifier:
    """Intelligent classification and scoring engine for Reddit posts."""

    def __init__(self, worthy_threshold: float = 80.0):
        self.worthy_threshold = worthy_threshold

    def extract_github_repos(self, text: str) -> List[str]:
        """Finds distinct GitHub repository links in text."""
        repos = []
        seen = set()
        for match in GITHUB_REPO_REGEX.finditer(text):
            owner = match.group(1).rstrip(".,;)>")
            repo = match.group(2).rstrip(".,;)>")
            if repo.lower().endswith(".git"):
                repo = repo[:-4]
            # Filter out non-repo GitHub subpaths
            if owner.lower() in {"about", "features", "pricing", "topics", "collections", "events", "trending"}:
                continue
            full_repo = f"https://github.com/{owner}/{repo}"
            if full_repo.lower() not in seen:
                seen.add(full_repo.lower())
                repos.append(full_repo)
        return repos

    def evaluate(self, post: Dict[str, Any], sub_weight: float = 1.0) -> Dict[str, Any]:
        """
        Calculates confidence score, detects noise/signals, and generates 2-3 line technical brief.
        """
        title = post.get("title", "")
        content = post.get("content", "") or post.get("summary", "")
        full_text = f"{title}\n{content}"
        full_text_lower = full_text.lower()

        score = 50.0  # Baseline neutral score
        factors = []

        # 1. GitHub Repository Extraction & Signal Bonus
        github_repos = self.extract_github_repos(full_text)
        if github_repos:
            bonus = 25.0
            score += bonus
            factors.append({"name": "Discovered GitHub Repository", "delta": f"+{bonus} pts", "detail": github_repos[0]})
        
        # 2. Technical Keyword Density
        matched_keywords = []
        tech_score = 0.0
        for kw, pts in TECH_KEYWORDS.items():
            if kw in full_text_lower:
                matched_keywords.append(kw)
                tech_score += pts
        tech_score = min(tech_score, 25.0)  # Capped at +25
        if tech_score > 0:
            score += tech_score
            factors.append({
                "name": "High-Signal Engineering Density",
                "delta": f"+{round(tech_score, 1)} pts",
                "detail": f"Matched: {', '.join(matched_keywords[:6])}"
            })

        # 3. Actionable Implementation & Code Artifacts
        if "```" in full_text or "def " in full_text or "const " in full_text or "fn " in full_text:
            score += 10.0
            factors.append({"name": "Code Snippet / Implementation Included", "delta": "+10 pts", "detail": "Contains direct executable code syntax"})
        elif "\n- " in full_text or "\n1. " in full_text:
            score += 5.0
            factors.append({"name": "Structured Architectural Breakdown", "delta": "+5 pts", "detail": "Contains bulleted architectural specs"})

        # 4. Content Depth Check
        word_count = len(full_text.split())
        if word_count > 150:
            score += 8.0
            factors.append({"name": "In-Depth Post (150+ words)", "delta": "+8 pts", "detail": f"{word_count} words"})
        elif word_count < 25 and not github_repos:
            penalty = 20.0
            score -= penalty
            factors.append({"name": "Ultra-Short Post Penalty", "delta": f"-{penalty} pts", "detail": "Lacks sufficient technical substance"})

        # 5. Noise & Grievance Penalties
        for pattern, penalty, reason in NOISE_PATTERNS:
            if re.search(pattern, full_text_lower):
                score -= penalty
                factors.append({"name": f"Noise Penalty: {reason}", "delta": f"-{penalty} pts", "detail": reason})

        # Apply Subreddit Multiplier
        final_score = max(5.0, min(99.0, score * sub_weight))
        final_score = round(final_score, 1)

        is_worthy = final_score >= self.worthy_threshold

        # Generate 2-3 Line Engineering Synthesis
        synthesis = self._synthesize(title, content, github_repos, matched_keywords)

        return {
            "title": title,
            "url": post.get("url", ""),
            "author": post.get("author", "unknown"),
            "published_at": post.get("published_at", ""),
            "subreddit": post.get("subreddit", "Unknown"),
            "confidence_score": final_score,
            "is_worthy": is_worthy,
            "verdict": "WORTHY" if is_worthy else "FILTERED_NOISE",
            "github_repos": github_repos,
            "matched_keywords": matched_keywords[:8],
            "factors": factors,
            "synthesis": synthesis,
            "category": post.get("category", "General Tech")
        }

    def _synthesize(self, title: str, content: str, repos: List[str], keywords: List[str]) -> List[str]:
        """Synthesizes a structured 2-3 line technical brief."""
        lines = []
        
        clean_title = re.sub(r"\[.*?\]|\(.*?\)", "", title).strip()
        if repos:
            repo_name = repos[0].replace("https://github.com/", "")
            lines.append(f"**Tool & Solution:** Open-source project `{repo_name}` addressing developer workflows for {clean_title[:80]}.")
        else:
            lines.append(f"**Subject:** In-depth technical breakdown of {clean_title[:90]}.")

        if keywords:
            kw_str = ", ".join(keywords[:4])
            lines.append(f"**Architecture & Tech:** Employs architectural paradigms around {kw_str} to ensure deterministic, scalable behavior.")
        else:
            lines.append("**Architecture & Tech:** Practical production implementation tested across modern runtime environments.")

        if repos:
            lines.append(f"**Takeaway:** Verified source code available at `{repos[0]}` for integration into autonomous agent pipelines.")
        else:
            lines.append("**Takeaway:** Directly applicable engineering lessons and configuration patterns to prevent common production pitfalls.")

        return lines
