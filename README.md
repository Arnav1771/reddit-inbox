# Reddit Inbox & High-Signal Radar

> **Autonomous SDE Intelligence Engine & Noise Classifier**  
> Published for **Arnav1771** · Built for local-first developer intelligence, open-source tool discovery, and zero-slop pair programming.

---

## ⚡ Overview

**Reddit Inbox** transforms engineering subreddits (`r/ClaudeCode`, `r/ClaudeAI`, `r/BestGitHubRepos`, `r/UI_Design`, `r/web_design`, `r/projects`, `r/LocalLLaMA`) into an actionable, strictly curated technical radar. Instead of drowning in speculative hype, service outage complaints, billing questions, or generic AI slop, Reddit Inbox evaluates posts using a multi-factor confidence scoring pipeline.

Only posts meeting a **≥80.0% confidence score** are promoted to the executive Markdown Vault and interactive dashboard. Everything else is quarantined.

---

## 🛡️ "Learn, Understand, Worthy" Intelligence Architecture

```
                                 [Reddit RSS / Atom Feeds]
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │       Feed Crawler Engine     │
                             │ (Direct RSS + Salamance Relay)│
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │      Classifier & Scorer      │
                             │  • Tech Density Keywords      │
                             │  • GitHub Repo Extractor      │
                             │  • Grievance / Outage Filter  │
                             └───────────────┬───────────────┘
                                             │
                         ┌───────────────────┴───────────────────┐
                         ▼                                       ▼
             Confidence Score ≥ 80.0%                Confidence Score < 80.0%
                         │                                       │
                         ▼                                       ▼
             ┌───────────────────────┐               ┌───────────────────────┐
             │      WORTHY INBOX     │               │   QUARANTINE AUDIT    │
             │ • 2-3 Line Brief      │               │ • Filtered Complaints │
             │ • Discovered Repos    │               │ • Deduplicated Spam   │
             │ • vault/RADAR.md      │               │ • data/quarantine.json│
             │ • web/data.json       │               └───────────────────────┘
             └───────────────────────┘
```

### 1. The Confidence Scoring Rubric
- **GitHub Repository Extracted:** `+25.0 pts` (Detects and normalizes GitHub project links)
- **High-Signal Technical Density:** Up to `+25.0 pts` (Matches: `MCP`, `worktree`, `prompt cache TTL`, `structured output`, `AST decompilation`, `WebRTC`, `SQLite`, `design tokens`, `spring physics`, etc.)
- **Executable Code Snippet or Specs:** `+10.0 pts` (Executable syntax or structured architectural blueprints)
- **Substance & Depth Check:** `+8.0 pts` for detailed write-ups (150+ words); `-20.0 pts` for ultra-short vague posts.
- **Noise & Grievance Penalties:**
  - Outage / Server status complaints: `-40.0 pts`
  - Billing, refund, or subscription tickets: `-35.0 pts`
  - Account suspension / ban grievances: `-35.0 pts`
  - Low-effort AI wrappers & dropshipping: `-45.0 pts`
  - Generic speculative fluff ("Is coding dead?"): `-25.0 pts`

### 2. High-Signal 2-3 Line Brief Format
Every promoted post receives a standardized technical brief:
1. **Tool & Solution:** Identifies the project and the concrete developer problem solved.
2. **Architecture & Tech:** Explains the engineering stack, protocol, or design mechanism.
3. **Takeaway:** Provides the exact GitHub repository link or actionable takeaway for pair programming.

---

## 🚀 Quick Start (Zero External Dependencies)

Reddit Inbox runs entirely on Python 3's standard library. No `pip install` required.

```bash
# 1. Initialize repository and seed baseline high-signal intelligence
python -m src.cli init

# 2. Run diagnostics & connectivity check
python -m src.cli doctor

# 3. Synchronize monitored subreddits
python -m src.cli sync

# 4. Launch the local Google Stitch dark-mode dashboard
python -m src.cli serve --port 8085
```

Open [http://localhost:8085](http://localhost:8085) to view the live dashboard.

---

## 💻 CLI Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `init` | Initialize folders, seed intelligence, generate vault | `python -m src.cli init` |
| `doctor` | Diagnostics, file permissions, and network checks | `python -m src.cli doctor` |
| `sync` | Fetch feeds, calculate confidence scores, update vault | `python -m src.cli sync --threshold 80.0` |
| `eval` | Evaluate an ad-hoc post or text snippet with factor breakdown | `python -m src.cli eval --text "We built fast-mcp in Rust..."` |
| `serve` | Launch local Google Stitch web dashboard | `python -m src.cli serve --port 8085` |
| `stats` | Display signal-to-noise metrics & discovered repos | `python -m src.cli stats` |

---

## 🎨 Interactive Dashboard (Google Stitch Specification)

The built-in web viewer adheres to anti-slop design standards:
- **Deep Slate Palette:** Canvas (`#070a13`), cards (`#0e1628`), subtle borders (`#1e293b`), crisp typography (`Plus Jakarta Sans` and `JetBrains Mono`).
- **Interactive Confidence Slider:** Drag between 60% and 95% to inspect how thresholding adjusts the promoted stream in real time.
- **One-Click Git Clone:** Instantly copy `git clone <repo>` commands to clipboard.
- **Transparent Scoring Breakdown:** Expandable accordions on every card showing every delta point and matched keyword.
- **Quarantine Audit Toggle:** Inspect filtered posts and understand why they failed the signal gate.

---

## 📁 Repository Structure

```text
reddit-inbox/
├── src/
│   ├── config.py          # Subreddits, network headers, and scoring weights
│   ├── classifier.py      # 'Learn, Understand, Worthy' confidence engine
│   ├── feed_crawler.py    # Resilient Atom/RSS reader & HTML sanitization
│   ├── vault.py           # Markdown generator & JSON persistence
│   ├── seeds.py           # Baseline verified high-signal intelligence
│   └── cli.py             # CLI commands (init, doctor, sync, eval, serve, stats)
├── web/
│   ├── index.html         # Responsive Google Stitch dashboard
│   ├── style.css          # Anti-slop dark CSS design tokens
│   ├── app.js             # Real-time filtering, search, and slider logic
│   └── data.json          # Live dataset generated by vault
├── vault/
│   ├── RADAR.md           # Executive briefing of curated ≥80% posts
│   ├── REPOSITORIES.md    # Catalog of discovered GitHub tools
│   └── DESIGN_SYSTEMS.md  # Curated UI/UX guidelines and anti-slop rules
├── tests/
│   ├── test_classifier.py # Unit tests for scoring & noise rejection
│   ├── test_crawler.py    # Unit tests for Atom XML parsing
│   └── test_vault.py      # Unit tests for vault generation
└── README.md
```

---

## 🧪 Testing

Run the test suite using Python's standard `unittest`:

```bash
python -m unittest discover tests
```

---

## 📄 License

MIT © Arnav Bhargava (`Arnav1771`)
