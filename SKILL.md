---
name: my-30days-research
description: Research any topic across Hacker News, GitHub, and DEV Community over the last 30 days and synthesize a cited brief or detect unbuilt micro-SaaS opportunities
---

# 30-Day Multi-Source Community Research & Idea Mining Engine

This skill equips an AI agent to research any topic across three authentic developer communities from the past 30 days:
1. **Hacker News:** High-signal discussions, founder perspectives, and technical debates.
2. **DEV Community:** Real developer tutorials, architecture writeups, and experiences.
3. **GitHub:** Trending open-source tools and repositories ranked by stars.

It then uses Google's free Gemini Flash model to synthesize the findings into either:
- **`--mode brief` (Default):** The **Hype vs. Reality** filter (The Promise, The Reality Check, The Verdict, and Trending Code).
- **`--mode ideas`:** The **Unbuilt Opportunities** detector (mining real developer complaints to formulate 3 concrete micro-SaaS or tool ideas with target users and weekend MVPs).

Every run updates an interactive, dark-mode visual magazine at `briefs/index.html` and saves a timestamped Markdown report.

---

## When to Use This Skill

Activate this skill when:
- The user asks: *"What are people saying about [topic] in the last 30 days?"*
- The user asks: *"What problems or tool ideas exist in [topic] right now?"* (`--mode ideas`)
- Researching recent community sentiment, tool releases, or alternatives to a framework.
- Investigating real-world friction and gotchas before adopting a technology.

---

## How to Run the Tool

Execute the Python research script from the project root:

### 1. The Hype vs. Reality Brief (Default)
```bash
python research.py "<topic>"
# or explicitly:
python research.py "<topic>" --mode brief
```

### 2. The Unbuilt Opportunities Detector
```bash
python research.py "<topic>" --mode ideas
```

### Example Invocations:
```bash
python research.py "AI agents" --mode ideas
python research.py "Local LLMs" --mode brief
python research.py "Rust web frameworks"
```

---

## Interactive Local Magazine Dashboard

After running any search, open the generated HTML dashboard in any browser:
```text
briefs/index.html
```
Features:
- **Dark Mode UI:** Modern, clean magazine layout.
- **Sidebar Archive:** Browse, search, and filter all past research briefs.
- **One-Click Copy:** Easily copy the formatted markdown for notes or reports.
- **Direct Citations:** Clickable links to every underlying discussion thread and repository.

---

## Prerequisites (100% Free)

1. **Python 3.10+** (uses standard libraries and `curl_cffi`).
2. **Google Gemini API Key:**
   - Grab a free key at [Google AI Studio](https://aistudio.google.com/).
   - Place it inside `.env`:
     ```env
     GEMINI_API_KEY=your_key_here
     ```
