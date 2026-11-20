# RealityCheck 30D

An open-source research engine that skips marketing hype and uncovers what developers are genuinely building, debating, and struggling with across the live community web over the past 30 days.

Powered by free community data sources and Google's free Gemini Flash model.

---
<img width="1336" height="585" alt="image" src="https://github.com/user-attachments/assets/db6300ac-4e6b-43df-93ae-e41ba82d36c1" />


## Why RealityCheck?

Traditional search results are frequently saturated with search-engine-optimized posts and promotional articles. RealityCheck bypasses that noise by directly querying active practitioner communities:

* **Hacker News:** Real discussions, founder feedback, and architecture debates.
* **DEV Community:** Authentic developer writeups, tutorials, and practical hurdles.
* **GitHub:** Community-starred repositories and new open-source releases.

---

## Key Capabilities

### 1. The Hype vs. Reality Filter (`--mode brief`)
Generates an objective summary split into:
* **The Promise:** What the community is genuinely excited about.
* **The Reality Check:** Production gotchas, limitations, bundle regressions, and complaints.
* **The Verdict:** An honest evaluation of whether the tech is production-ready today.
* **Every takeaway is backed by direct URLs** to the source discussions.

### 2. The Unbuilt Opportunities Detector (`--mode ideas`)
Analyzes real complaints and friction points in the community to surface **3 concrete tool or micro-SaaS opportunities**, complete with:
* Target audience
* The specific problem being solved
* Community evidence links
* A realistic blueprint to build the first version in a weekend

### 3. Smart Query & Version Cascade
Searching for specific version numbers (like `Next.js 15` or `Python 3.14`) often returns zero results on strict platform tags. RealityCheck automatically creates a smart fallback cascade (e.g. `Next.js 15` -> `Next.js` -> `nextjs`) so your searches never return empty.

### 4. Local Visual Magazine Dashboard
Every search automatically archives a Markdown report and updates an interactive, self-contained local web magazine at `briefs/index.html`. It includes a search filter, past reports sidebar, and a one-click copy button.

---

## Getting Started

### Prerequisites
* Python 3.10 or newer
* A free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/) (no credit card required)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/realitycheck-30d.git
   cd realitycheck-30d
   ```

2. **Install dependencies:**
   ```bash
   pip install curl_cffi
   ```

3. **Configure your free API key:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and add your key:
   ```env
   GEMINI_API_KEY=your_actual_key_here
   ```

---

## Usage

```bash
# Generate a Hype vs. Reality brief (default)
python research.py "AI agents"
python research.py "Next.js 15" --mode brief

# Discover unbuilt micro-SaaS opportunities
python research.py "AI agents" --mode ideas
python research.py "Local LLMs" --mode ideas
```

### Viewing Your Dashboard
Open `briefs/index.html` in your web browser to browse your past research briefs in an offline-ready dark-mode interface.

---

## License

Released under the [MIT License](LICENSE).

