"""
=============================================================================
MULTI-SOURCE RESEARCH ENGINE WITH AI BRAIN (GEMINI POWERED)
=============================================================================
Welcome! This script gathers fresh community conversations, discussions,
and open-source projects across three rock-solid, 100% free community APIs:
  1. Hacker News (Technologists, founders, and engineers)
  2. DEV Community (Developer tutorials, perspectives, and experiences)
  3. GitHub (Top trending open-source tools and repositories)

It offers two distinctive AI thinking modes:
  - 'brief': The "Hype vs. Reality" breakdown (Promise, Reality Check, Verdict)
  - 'ideas': The "Unbuilt Opportunities" detector (mining real complaints for tools)

Every run saves a Markdown brief in `briefs/` and updates a local, self-contained
dark-mode web magazine at `briefs/index.html`!

HOW TO RUN:
    python research.py "AI agents"
    python research.py "AI agents" --mode ideas
    python research.py "Local LLMs" --mode brief
=============================================================================
"""

import os
import re
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
from datetime import datetime

# Optional browser impersonator for platforms that require browser handshakes
try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

# Hacker News search from fetch_hn.py
try:
    from fetch_hn import search_hacker_news
except ImportError:
    search_hacker_news = None


# ---------------------------------------------------------------------------
# SECTION 1: SETTINGS & CONFIGURATION
# ---------------------------------------------------------------------------
# Tweak these numbers anytime to adjust how much data you want to collect!
# ---------------------------------------------------------------------------
TOP_COUNT_PER_SOURCE = 5    # How many items to display per community
DEV_FETCH_SIZE = 10         # How many DEV.to articles to fetch
DAYS_BACK_HN = 30           # Number of days to look back for Hacker News
GEMINI_MODEL = "gemini-2.5-flash"  # Fast, smart, and free on Google AI Studio
BRIEFS_DIR = os.path.join(os.path.dirname(__file__), "briefs")


# ---------------------------------------------------------------------------
# SECTION 2: ENVIRONMENT LOADER (.ENV)
# ---------------------------------------------------------------------------
# Reads GEMINI_API_KEY from your local .env file without external dependencies.
# ---------------------------------------------------------------------------
def load_environment_variables():
    """Reads key-value pairs from a local .env file in the same directory."""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip().strip('"').strip("'")
        except Exception as error:
            print(f"  [Notice] Could not read .env file: {error}")

    return env_vars


def get_gemini_api_key():
    """Gets the Gemini key from system environment or local .env file."""
    key = os.environ.get("GEMINI_API_KEY")
    if key and key != "paste_your_key_here":
        return key

    env_vars = load_environment_variables()
    key = env_vars.get("GEMINI_API_KEY")
    if key and key != "paste_your_key_here":
        return key

    return None


# ---------------------------------------------------------------------------
# SECTION 3: QUERY CLEANING & VERSION FALLBACK HELPER
# ---------------------------------------------------------------------------
# When users search with specific version numbers (e.g. 'Next.js 15', 'Python 3.14'),
# strict platform tag systems and search filters might return 0 matches.
# This helper creates a smart cascade of query variations so searches never fail!
# ---------------------------------------------------------------------------
def generate_query_variations(topic: str):
    """
    Produces smart query fallbacks by stripping version numbers and punctuation.
    Example: 'Next.js 15' -> ['Next.js 15', 'Next.js', 'Nextjs']
    """
    variations = [topic.strip()]
    
    # 1. Strip version numbers (e.g. ' 15', ' 3.14', ' v2', ' 2.0')
    no_version = re.sub(r'(\s+v?\d+(\.\d+)*|\b\d+(\.\d+)+\b)', '', topic, flags=re.IGNORECASE).strip()
    if no_version and no_version.lower() != topic.lower():
        variations.append(no_version)
        
    # 2. Strip dots for common framework names: 'Next.js' -> 'Nextjs'
    no_dots = topic.replace(".", "").strip()
    if no_dots.lower() not in [v.lower() for v in variations]:
        variations.append(no_dots)
        
    # 3. Strip dots from the version-less query: 'Next.js' without version -> 'Nextjs'
    if no_version:
        no_dots_version = no_version.replace(".", "").strip()
        if no_dots_version.lower() not in [v.lower() for v in variations]:
            variations.append(no_dots_version)
            
    return variations


# ---------------------------------------------------------------------------
# SECTION 4: HACKER NEWS FETCHER (WITH SMART FALLBACK)
# ---------------------------------------------------------------------------
def fetch_hacker_news_posts(topic: str):
    """
    Fetches top Hacker News stories from the past 30 days.
    If the exact query (e.g. 'Next.js 15') returns 0 stories, it automatically
    retries with broader variations (e.g. 'Next.js' or 'Nextjs').
    """
    query_candidates = generate_query_variations(topic)
    raw_hits = []

    for candidate in query_candidates:
        try:
            if search_hacker_news:
                hits = search_hacker_news(candidate)
            else:
                cutoff = int(time.time()) - (DAYS_BACK_HN * 24 * 60 * 60)
                params = {
                    "query": candidate,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{cutoff}",
                    "hitsPerPage": 50,
                }
                url = f"https://hn.algolia.com/api/v1/search?{urllib.parse.urlencode(params)}"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    hits = json.loads(resp.read().decode("utf-8")).get("hits", [])

            if hits:
                raw_hits = hits
                if candidate.lower() != topic.lower():
                    print(f"     [HN Fallback] Exact term had 0 recent stories; matched {len(hits)} under '{candidate}'!")
                break
        except Exception as error:
            print(f"  [Hacker News Notice] {type(error).__name__}: {error}")
            continue

    posts = []
    for hit in raw_hits:
        item_id = hit.get("objectID")
        hn_url = f"https://news.ycombinator.com/item?id={item_id}"
        posts.append({
            "title": hit.get("title") or "Untitled Story",
            "score": hit.get("points") or 0,
            "comments": hit.get("num_comments") or 0,
            "url": hit.get("url") or hn_url,
            "discussion": hn_url
        })

    posts.sort(key=lambda item: item["score"], reverse=True)
    return posts[:TOP_COUNT_PER_SOURCE]


# ---------------------------------------------------------------------------
# SECTION 5: DEV COMMUNITY FETCHER (DEV.TO API WITH TAG CASCADE)
# ---------------------------------------------------------------------------
def fetch_dev_to_articles(topic: str):
    """
    Fetches top articles from DEV Community over the past 30 days.
    Generates a smart cascade of tag candidates, stripping version numbers
    and symbols so searches like 'Next.js 15' automatically match 'nextjs' or 'react'.
    """
    candidates = []
    
    # 1. Clean alphanumeric from raw topic (e.g. 'nextjs15')
    tag1 = re.sub(r"[^a-zA-Z0-9]", "", topic.lower())
    if tag1:
        candidates.append(tag1)
        
    # 2. Tag without version numbers (e.g. 'nextjs' from 'Next.js 15')
    no_ver = re.sub(r'(\s*v?\d+(\.\d+)*|\b\d+(\.\d+)+\b)', '', topic, flags=re.IGNORECASE)
    tag2 = re.sub(r"[^a-zA-Z]", "", no_ver.lower())
    if tag2 and tag2 not in candidates:
        candidates.append(tag2)
        
    # 3. First word stripped (e.g. 'next' or 'python')
    first_word = topic.strip().split()[0].lower() if topic.strip() else ""
    tag3 = re.sub(r"[^a-zA-Z]", "", first_word)
    if tag3 and tag3 not in candidates:
        candidates.append(tag3)

    articles = []
    headers = {
        "User-Agent": "CommunityResearchTool/1.0 (Educational open-source research)",
        "Accept": "application/json"
    }

    used_tag = None
    for tag in candidates:
        url = f"https://dev.to/api/articles?tag={tag}&top=30&per_page={DEV_FETCH_SIZE}"
        try:
            if cffi_requests:
                resp = cffi_requests.get(url, impersonate="chrome", timeout=12)
                if resp.status_code == 200:
                    raw_data = resp.json()
                    if raw_data:
                        articles = raw_data
                        used_tag = tag
                        break
            else:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as r:
                    raw_data = json.loads(r.read().decode("utf-8"))
                    if raw_data:
                        articles = raw_data
                        used_tag = tag
                        break
        except Exception:
            continue

    if used_tag and used_tag != tag1:
        print(f"     [DEV Fallback] Matched DEV Community discussions under tag '{used_tag}'!")

    results = []
    for art in articles:
        title = art.get("title") or "Untitled Article"
        reactions = art.get("positive_reactions_count") or art.get("public_reactions_count") or 0
        comments = art.get("comments_count") or 0
        article_url = art.get("url") or ""
        author = art.get("user", {}).get("name") or "Community Author"

        results.append({
            "title": title,
            "score": reactions,
            "comments": comments,
            "author": author,
            "url": article_url
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:TOP_COUNT_PER_SOURCE]


# ---------------------------------------------------------------------------
# SECTION 6: GITHUB REPOSITORIES FETCHER (WITH FALLBACK)
# ---------------------------------------------------------------------------
def fetch_github_repos(topic: str):
    """
    Fetches trending GitHub repositories sorted by stars.
    Falls back to broader query terms if the exact version yields 0 repos.
    """
    query_candidates = generate_query_variations(topic)
    items = []

    for candidate in query_candidates:
        encoded_topic = urllib.parse.quote_plus(candidate)
        url = f"https://api.github.com/search/repositories?q={encoded_topic}&sort=stars&order=desc&per_page={TOP_COUNT_PER_SOURCE}"

        try:
            if cffi_requests:
                resp = cffi_requests.get(url, impersonate="chrome", timeout=12)
                raw_json = resp.json()
            else:
                headers = {"User-Agent": "CommunityResearchTool/1.0", "Accept": "application/json"}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as r:
                    raw_json = json.loads(r.read().decode("utf-8"))

            found = raw_json.get("items", [])
            if found:
                items = found
                if candidate.lower() != topic.lower():
                    print(f"     [GitHub Fallback] Matched repositories under '{candidate}'!")
                break
        except Exception as error:
            print(f"  [GitHub Notice] {type(error).__name__}: {error}")
            continue

    repos = []
    for item in items:
        name = item.get("full_name") or item.get("name") or "Unnamed Repo"
        stars = item.get("stargazers_count") or 0
        desc = item.get("description") or "No description provided."
        html_url = item.get("html_url") or ""

        repos.append({
            "name": name,
            "stars": stars,
            "description": desc,
            "url": html_url
        })

    return repos


# ---------------------------------------------------------------------------
# SECTION 6: AI BRAIN (GEMINI WITH 'BRIEF' AND 'IDEAS' MODES)
# ---------------------------------------------------------------------------
# - Mode 'brief': Generates the "Hype vs. Reality" breakdown.
# - Mode 'ideas': Mines real complaints and gaps to detect 3 unbuilt opportunities.
# ---------------------------------------------------------------------------
def build_community_data_text(hn_posts, dev_articles, gh_repos):
    """Combines community discussions into a single structured text block."""
    context_lines = []
    
    if hn_posts:
        context_lines.append("--- HACKER NEWS RECENT DISCUSSIONS (PAST 30 DAYS) ---")
        for item in hn_posts:
            context_lines.append(f"- Title: {item['title']}")
            context_lines.append(f"  Upvotes: {item['score']} | Comments: {item['comments']}")
            context_lines.append(f"  URL: {item['url']}\n")

    if dev_articles:
        context_lines.append("--- DEV COMMUNITY ARTICLES (PAST 30 DAYS) ---")
        for art in dev_articles:
            context_lines.append(f"- Article: {art['title']} by {art.get('author', 'Author')}")
            context_lines.append(f"  Reactions: {art['score']} | Comments: {art['comments']}")
            context_lines.append(f"  URL: {art['url']}\n")

    if gh_repos:
        context_lines.append("--- GITHUB TRENDING REPOSITORIES ---")
        for repo in gh_repos:
            context_lines.append(f"- Project: {repo['name']} ({repo['stars']} stars)")
            context_lines.append(f"  Description: {repo['description']}")
            context_lines.append(f"  URL: {repo['url']}\n")

    return "\n".join(context_lines)


def generate_ai_brief(topic: str, hn_posts: list, dev_articles: list, gh_repos: list, api_key: str, mode: str = "brief"):
    """
    Synthesizes findings into either:
      1. Hype vs. Reality Brief (mode='brief')
      2. Unbuilt Opportunities Detector (mode='ideas')
    """
    raw_data_text = build_community_data_text(hn_posts, dev_articles, gh_repos)

    if mode == "ideas":
        # -----------------------------------------------------------------------
        # OPTION 2: UNBUILT OPPORTUNITIES DETECTOR PROMPT
        # -----------------------------------------------------------------------
        prompt = f"""You are an entrepreneurial product researcher and software architect.

Topic: "{topic}"

Below are real community conversations, complaints, tutorials, and repositories from the past 30 days.

Your goal is to inspect the pain points, frustrations, and friction people are experiencing and discover **3 Concrete Unbuilt Tool / Micro-SaaS Opportunities**.

Write a clean, human, and exciting Markdown brief titled "# 💡 30-DAY UNBUILT OPPORTUNITIES: {topic.upper()}":

1. **The Friction Landscape**: A short 2-3 sentence overview of what is currently painful, slow, or broken in this space based on the community chatter.
2. **3 Concrete Tool / Project Opportunities**:
   For each idea provide:
   - **Idea Name & Tagline**: A catchy, clear project name and 1-sentence value proposition.
   - **Target User**: Exactly who needs this (e.g. solo dev, audit team, DevOps engineer).
   - **The Pain Point Solved**: The specific complaint or gap it fixes.
   - **Community Evidence**: You MUST cite the exact URL where someone struggled or showed this need, formatted as [Source Name](URL).
   - **MVP in a Weekend**: How a solo developer could build the first version in 48 hours without spending money.
3. **The Bottom Line**: One encouraging, grounded closing thought on which of these 3 has the fastest path to real adoption.

Tone: Authentic, constructive, deeply practical, and free of corporate jargon.

COMMUNITY DATA:
{raw_data_text}
"""
    else:
        # -----------------------------------------------------------------------
        # OPTION 1: HYPE VS. REALITY BRIEF PROMPT
        # -----------------------------------------------------------------------
        prompt = f"""You are a candid, senior technical analyst doing a 30-day pulse check.

Topic: "{topic}"

Below are recent community conversations (Hacker News), practical developer writeups (DEV Community), and top repositories (GitHub).

Write a clear, thoughtful "30-DAY HYPE VS. REALITY EXECUTIVE BRIEF" in clean Markdown:

1. **Executive Overview**: A short 2-3 sentence summary of where developer sentiment sits right now.
2. **🟢 The Promise (What People Are Excited About)**:
   What people are celebrating, adopting, or trying to achieve. Back every point with exact source links [Source Name](URL).
3. **🔴 The Reality Check (Complaints, Gotchas & Limitations)**:
   What is actually breaking in production, security concerns, blocked access, or community pushback. Back every point with exact source links [Source Name](URL).
4. **⚖️ The Verdict**:
   An honest assessment: Is this genuinely ready for production today, or is it mostly hype and experimental toys? Who should adopt it now, and who should wait?
5. **🛠️ Trending Tools & Code**:
   A concise bullet list of notable repositories being starred, with direct links [Repo Name](URL).

Tone: Candid, grounded, human, direct, and zero marketing fluff.

COMMUNITY DATA:
{raw_data_text}
"""

    endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint_url,
            data=req_data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=35) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            candidates = resp_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "Could not generate brief from Gemini response."

    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode("utf-8")
        return f"Gemini API returned HTTP {http_err.code}: {err_body}"
    except Exception as err:
        return f"Error contacting Gemini API: {type(err).__name__} - {err}"


# ---------------------------------------------------------------------------
# SECTION 7: PERSISTENCE & DASHBOARD GENERATOR (OPTION 4)
# ---------------------------------------------------------------------------
# Saves each run to `briefs/<slug>-<mode>-YYYY-MM-DD.md` and rebuilds a
# self-contained dark-mode magazine at `briefs/index.html`.
# ---------------------------------------------------------------------------
def save_brief_to_file(topic: str, mode: str, ai_brief: str, hn_posts: list, dev_articles: list, gh_repos: list):
    """Saves the markdown brief and updates the interactive HTML dashboard."""
    os.makedirs(BRIEFS_DIR, exist_ok=True)
    
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic.strip().lower()).strip("-")
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{slug}-{mode}-{date_str}.md"
    file_path = os.path.join(BRIEFS_DIR, filename)

    mode_label = "Hype vs. Reality Brief" if mode == "brief" else "Unbuilt Opportunities"

    lines = [
        f"# 30-Day Research: {topic} ({mode_label})",
        f"*Generated on {date_str} via Hacker News, DEV Community, and GitHub*",
        "",
        "## AI Synthesis",
        ai_brief if ai_brief else "_AI summary was skipped (no API key in .env)._",
        "",
        "---",
        "## Underlying Sources & References",
        "",
        f"### Hacker News Discussions ({len(hn_posts)})",
    ]
    for idx, item in enumerate(hn_posts, start=1):
        lines.append(f"{idx}. [{item['title']}]({item['url']}) - *{item['score']} upvotes, {item['comments']} comments*")

    lines.append(f"\n### DEV Community Articles ({len(dev_articles)})")
    for idx, art in enumerate(dev_articles, start=1):
        lines.append(f"{idx}. [{art['title']}]({art['url']}) by {art.get('author', 'Author')} - *{art['score']} reactions*")

    lines.append(f"\n### GitHub Repositories ({len(gh_repos)})")
    for idx, repo in enumerate(gh_repos, start=1):
        lines.append(f"{idx}. [{repo['name']}]({repo['url']}) (★ {repo['stars']}) - {repo['description']}")

    lines.append("")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as err:
        print(f"  [Notice] Could not save markdown brief: {err}")
        return None

    # Rebuild the interactive dashboard
    build_dashboard_html()

    return file_path


def build_dashboard_html():
    """
    Scans the `briefs/` directory and compiles a self-contained, beautiful
    dark-mode magazine dashboard into `briefs/index.html`.
    """
    if not os.path.exists(BRIEFS_DIR):
        return

    # Find all markdown files in briefs/
    md_files = [f for f in os.listdir(BRIEFS_DIR) if f.endswith(".md")]
    md_files.sort(reverse=True)  # Newest first

    briefs_data = []
    for f in md_files:
        full_path = os.path.join(BRIEFS_DIR, f)
        try:
            with open(full_path, "r", encoding="utf-8") as file:
                content = file.read()
            # Extract first heading as title
            match = re.search(r"^#\s+(.*)", content, re.MULTILINE)
            title = match.group(1) if match else f.replace(".md", "").replace("-", " ").title()
            
            # Determine mode
            mode_tag = "IDEAS" if "-ideas-" in f else "BRIEF"

            briefs_data.append({
                "filename": f,
                "title": title,
                "mode": mode_tag,
                "content": content
            })
        except Exception:
            continue

    briefs_json = json.dumps(briefs_data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>30-Day Research Magazine</title>
  <style>
    :root {{
      --bg: #0f141c;
      --sidebar-bg: #161d28;
      --card-bg: #1c2534;
      --border: #2b384e;
      --text-main: #e2e8f0;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.15);
      --green: #4ade80;
      --amber: #fbbf24;
      --tag-ideas: #a855f7;
      --tag-brief: #38bdf8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      display: flex;
      height: 100vh;
      overflow: hidden;
    }}
    /* Sidebar */
    #sidebar {{
      width: 320px;
      min-width: 280px;
      background: var(--sidebar-bg);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      height: 100%;
    }}
    .sidebar-header {{
      padding: 20px;
      border-bottom: 1px solid var(--border);
    }}
    .sidebar-header h1 {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .sidebar-search {{
      padding: 12px 20px;
      border-bottom: 1px solid var(--border);
    }}
    .sidebar-search input {{
      width: 100%;
      padding: 8px 12px;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text-main);
      font-size: 0.9rem;
      outline: none;
    }}
    .sidebar-search input:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 2px var(--accent-glow);
    }}
    #briefs-list {{
      flex: 1;
      overflow-y: auto;
      padding: 10px;
    }}
    .brief-card {{
      padding: 12px 14px;
      margin-bottom: 8px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .brief-card:hover {{
      border-color: var(--accent);
      transform: translateX(2px);
    }}
    .brief-card.active {{
      border-color: var(--accent);
      background: #222d3f;
      box-shadow: 0 0 12px var(--accent-glow);
    }}
    .brief-card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }}
    .badge {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .badge-brief {{ background: rgba(56, 189, 248, 0.2); color: var(--tag-brief); }}
    .badge-ideas {{ background: rgba(168, 85, 247, 0.2); color: var(--tag-ideas); }}
    .brief-card-title {{
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text-main);
      line-height: 1.3;
    }}
    .brief-card-date {{
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    /* Main Content Viewer */
    #viewer {{
      flex: 1;
      height: 100%;
      overflow-y: auto;
      padding: 40px 60px;
      display: flex;
      flex-direction: column;
    }}
    .top-toolbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 30px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }}
    .top-toolbar .doc-title {{
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--accent);
    }}
    .copy-btn {{
      padding: 8px 16px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text-main);
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }}
    .copy-btn:hover {{
      border-color: var(--accent);
      background: var(--sidebar-bg);
    }}
    /* Markdown Styles */
    #markdown-render {{
      max-width: 820px;
      line-height: 1.7;
      font-size: 1.02rem;
      color: #cbd5e1;
    }}
    #markdown-render h1 {{
      font-size: 1.8rem;
      font-weight: 800;
      color: #f8fafc;
      margin-bottom: 10px;
      letter-spacing: -0.02em;
    }}
    #markdown-render h2 {{
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--accent);
      margin-top: 30px;
      margin-bottom: 14px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 6px;
    }}
    #markdown-render h3 {{
      font-size: 1.1rem;
      font-weight: 600;
      color: #e2e8f0;
      margin-top: 22px;
      margin-bottom: 10px;
    }}
    #markdown-render p {{
      margin-bottom: 16px;
    }}
    #markdown-render ul, #markdown-render ol {{
      margin-left: 24px;
      margin-bottom: 18px;
    }}
    #markdown-render li {{
      margin-bottom: 8px;
    }}
    #markdown-render a {{
      color: var(--accent);
      text-decoration: none;
      border-bottom: 1px dotted var(--accent);
      transition: border 0.15s;
    }}
    #markdown-render a:hover {{
      border-bottom-style: solid;
    }}
    #markdown-render strong {{
      color: #f1f5f9;
      font-weight: 700;
    }}
    #markdown-render hr {{
      border: 0;
      height: 1px;
      background: var(--border);
      margin: 30px 0;
    }}
    #markdown-render blockquote {{
      border-left: 3px solid var(--accent);
      padding-left: 16px;
      color: var(--text-muted);
      margin-bottom: 16px;
      font-style: italic;
    }}
    .empty-state {{
      text-align: center;
      margin-top: 100px;
      color: var(--text-muted);
    }}
  </style>
</head>
<body>
  <div id="sidebar">
    <div class="sidebar-header">
      <h1>📰 Research Magazine</h1>
    </div>
    <div class="sidebar-search">
      <input type="text" id="searchInput" placeholder="Search saved briefs..." oninput="filterBriefs()">
    </div>
    <div id="briefs-list"></div>
  </div>

  <div id="viewer">
    <div class="top-toolbar">
      <div class="doc-title" id="activeTitle">Select a Brief</div>
      <button class="copy-btn" id="copyBtn" onclick="copyCurrentMarkdown()">📋 Copy Markdown</button>
    </div>
    <div id="markdown-render">
      <div class="empty-state">Select a research brief from the sidebar to view it.</div>
    </div>
  </div>

  <script>
    const briefs = {briefs_json};
    let activeIndex = 0;

    function renderMarkdown(md) {{
      let html = md
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/\\*\\*(.*?)\\*\\*/gim, '<strong>$1</strong>')
        .replace(/\\*(.*?)\\*/gim, '<em>$1</em>')
        .replace(/\\[([^\\]]+)\\]\\(([^\\)]+)\\)/gim, '<a href="$2" target="_blank" rel="noopener">$1</a>')
        .replace(/^\\s*-\\s+(.*$)/gim, '<li>$1</li>')
        .replace(/^---$/gim, '<hr>');

      // Wrap consecutive li in ul
      html = html.replace(/(<li>[\\s\\S]*?<\\/li>)/gim, '<ul>$1</ul>');
      html = html.replace(/<\\/ul>\\s*<ul>/gim, '');
      
      // Paragraphs
      html = html.split('\\n\\n').map(p => {{
        if (p.trim().startsWith('<h') || p.trim().startsWith('<ul') || p.trim().startsWith('<hr')) {{
          return p;
        }}
        return '<p>' + p.replace(/\\n/g, '<br>') + '</p>';
      }}).join('');

      return html;
    }}

    function selectBrief(index) {{
      activeIndex = index;
      const b = briefs[index];
      if (!b) return;

      document.getElementById('activeTitle').innerText = b.title;
      document.getElementById('markdown-render').innerHTML = renderMarkdown(b.content);

      document.querySelectorAll('.brief-card').forEach((el, idx) => {{
        el.classList.toggle('active', idx === index);
      }});
    }}

    function copyCurrentMarkdown() {{
      const b = briefs[activeIndex];
      if (!b) return;
      navigator.clipboard.writeText(b.content).then(() => {{
        const btn = document.getElementById('copyBtn');
        const oldText = btn.innerText;
        btn.innerText = '✅ Copied!';
        setTimeout(() => {{ btn.innerText = oldText; }}, 1800);
      }});
    }}

    function filterBriefs() {{
      const query = document.getElementById('searchInput').value.toLowerCase();
      const listEl = document.getElementById('briefs-list');
      listEl.innerHTML = '';

      briefs.forEach((b, index) => {{
        if (b.title.toLowerCase().includes(query) || b.content.toLowerCase().includes(query)) {{
          const card = document.createElement('div');
          card.className = 'brief-card' + (index === activeIndex ? ' active' : '');
          card.onclick = () => selectBrief(index);

          const badgeClass = b.mode === 'IDEAS' ? 'badge badge-ideas' : 'badge badge-brief';
          card.innerHTML = `
            <div class="brief-card-header">
              <span class="${{badgeClass}}">${{b.mode}}</span>
            </div>
            <div class="brief-card-title">${{b.title}}</div>
            <div class="brief-card-date">${{b.filename.split('-').slice(-3).join('-').replace('.md', '')}}</div>
          `;
          listEl.appendChild(card);
        }}
      }});
    }}

    // Initial render
    filterBriefs();
    if (briefs.length > 0) {{
      selectBrief(0);
    }}
  </script>
</body>
</html>"""

    dashboard_path = os.path.join(BRIEFS_DIR, "index.html")
    try:
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as err:
        print(f"  [Notice] Could not write dashboard HTML: {err}")


# ---------------------------------------------------------------------------
# SECTION 8: TERMINAL DISPLAY
# ---------------------------------------------------------------------------
def display_full_report(topic: str, mode: str, ai_brief: str, hn_posts: list, dev_articles: list, gh_repos: list, saved_path: str):
    """Prints the brief and raw sources to the terminal."""
    mode_header = "30-DAY UNBUILT OPPORTUNITIES DETECTOR" if mode == "ideas" else "30-DAY HYPE VS. REALITY BRIEF"
    
    print("\n" + "=" * 80)
    print(f"  {mode_header}: {topic.upper()}")
    print("=" * 80)

    if ai_brief:
        print("\n" + ai_brief.strip() + "\n")
    else:
        print("\n  [AI Brief Skipped] Add your free Gemini key to .env to generate this section!\n")

    print("=" * 80)
    print("  RAW COMMUNITY SOURCES & CITATIONS")
    print("=" * 80)

    # 1. Hacker News
    print(f"\n[+] HACKER NEWS STORIES ({len(hn_posts)} found):")
    if not hn_posts:
        print("    No stories found.")
    for idx, item in enumerate(hn_posts, start=1):
        print(f"    {idx}. {item['title']} ({item['score']} upvotes, {item['comments']} comments)")
        print(f"       Link: {item['url']}")

    # 2. DEV Community
    print(f"\n[+] DEV COMMUNITY ARTICLES ({len(dev_articles)} found):")
    if not dev_articles:
        print("    No DEV Community articles found.")
    for idx, art in enumerate(dev_articles, start=1):
        print(f"    {idx}. {art['title']} by {art.get('author', 'Author')} ({art['score']} reactions)")
        print(f"       Link: {art['url']}")

    # 3. GitHub
    print(f"\n[+] GITHUB REPOSITORIES ({len(gh_repos)} found):")
    if not gh_repos:
        print("    No repositories found.")
    for idx, repo in enumerate(gh_repos, start=1):
        print(f"    {idx}. {repo['name']} (★ {repo['stars']})")
        print(f"       {repo['description']}")
        print(f"       Link: {repo['url']}")

    print("\n" + "=" * 80)
    if saved_path:
        dashboard_url = os.path.join(BRIEFS_DIR, "index.html")
        print(f"  [Saved] Markdown Report: {saved_path}")
        print(f"  [Dashboard] Local Web Magazine: {dashboard_url}")
    print("=" * 80 + "\n")


# ---------------------------------------------------------------------------
# SECTION 9: MAIN PROGRAM FLOW & ARGPARSE
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Multi-Source Community Research & Idea Mining Engine")
    parser.add_argument("topic", nargs="?", default="", help="Topic to research (e.g. 'AI agents', 'Local LLMs')")
    parser.add_argument(
        "--mode",
        choices=["brief", "ideas"],
        default="brief",
        help="Mode: 'brief' (Hype vs. Reality breakdown) or 'ideas' (Unbuilt Opportunities detector)"
    )

    args = parser.parse_args()
    topic = args.topic.strip()
    mode = args.mode

    if not topic:
        try:
            topic = input("What topic would you like to explore? ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Have a wonderful day!")
            return

    if not topic:
        print("Please provide a topic to begin.")
        return

    mode_label = "Unbuilt Opportunities Detector" if mode == "ideas" else "Hype vs. Reality Brief"
    print(f"\nGathering community intelligence about: '{topic}' [{mode_label}]...")

    # 1. Fetch Hacker News
    print("  -> Searching Hacker News (past 30 days)...")
    hn_posts = fetch_hacker_news_posts(topic)

    # 2. Fetch DEV Community
    print("  -> Searching DEV Community (past 30 days)...")
    dev_articles = fetch_dev_to_articles(topic)

    # 3. Fetch GitHub Repositories
    print("  -> Searching GitHub repositories...")
    gh_repos = fetch_github_repos(topic)

    # 4. Check for Gemini API key
    gemini_key = get_gemini_api_key()
    ai_brief = ""

    if gemini_key:
        print(f"  -> Generating {mode_label} with Gemini Flash...")
        ai_brief = generate_ai_brief(topic, hn_posts, dev_articles, gh_repos, gemini_key, mode=mode)
    else:
        print("\n  [Tip] Want an AI brief? Add your free key to .env:")
        print("        GEMINI_API_KEY=your_key_here")

    # 5. Save report to briefs/ folder and update index.html
    saved_path = save_brief_to_file(topic, mode, ai_brief, hn_posts, dev_articles, gh_repos)

    # 6. Display to terminal
    display_full_report(topic, mode, ai_brief, hn_posts, dev_articles, gh_repos, saved_path)


if __name__ == "__main__":
    main()
