"""
=============================================================================
HACKER NEWS RESEARCH HELPER (LAST 30 DAYS)
=============================================================================
Welcome! This script helps you discover what real people in tech, startups,
and open source have been talking about over the past 30 days on Hacker News.

It uses Python's built-in standard libraries, meaning you do NOT need to
install anything extra (no pip install required).

HOW TO RUN:
    python fetch_hn.py "AI agents"
    
    Or simply run without arguments:
    python fetch_hn.py
    (It will ask you for a topic right in your terminal!)
=============================================================================
"""

import sys
import json
import time
import urllib.request
import urllib.parse


# ---------------------------------------------------------------------------
# SECTION 1: CONFIGURATION & SETTINGS
# ---------------------------------------------------------------------------
# Feel free to adjust these values to customize how far back you want to search
# or how many results you would like to see on your screen.
# ---------------------------------------------------------------------------
DAYS_BACK = 30             # How many days into the past to search (e.g. 7, 30, 60)
MAX_STORIES_TO_FETCH = 50 # How many stories to grab from the API before sorting
TOP_STORIES_TO_SHOW = 5   # How many of the highest-rated stories to display


# ---------------------------------------------------------------------------
# SECTION 2: FETCHING STORIES FROM HACKER NEWS
# ---------------------------------------------------------------------------
# This function queries the completely free Hacker News Algolia search API.
# No accounts, tokens, or credit cards are needed.
# ---------------------------------------------------------------------------
def search_hacker_news(topic: str):
    """
    Connects to the Hacker News Algolia API to search for recent story posts
    matching the given topic within the last DAYS_BACK days.
    """
    # Calculate the timestamp threshold (30 days ago from this very second)
    current_timestamp = int(time.time())
    cutoff_timestamp = current_timestamp - (DAYS_BACK * 24 * 60 * 60)

    # Set up search parameters:
    # - 'query': The search phrase you want to research
    # - 'tags': 'story' ensures we only get top-level stories/posts, not loose comments
    # - 'numericFilters': Restricts results to items posted after our cutoff date
    # - 'hitsPerPage': Number of records to inspect
    params = {
        "query": topic,
        "tags": "story",
        "numericFilters": f"created_at_i>{cutoff_timestamp}",
        "hitsPerPage": MAX_STORIES_TO_FETCH,
    }

    # Construct the full URL
    base_url = "https://hn.algolia.com/api/v1/search"
    full_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Add standard browser request headers so the public API doesn't mistake our request for bot spam
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    request = urllib.request.Request(full_url, headers=headers)

    try:
        # Open the connection and read the JSON response
        with urllib.request.urlopen(request, timeout=12) as response:
            raw_data = response.read().decode("utf-8")
            data = json.loads(raw_data)
            return data.get("hits", [])
    except Exception as error:
        print(f"\n[Notice] We couldn't fetch data from Hacker News right now: {error}")
        return []


# ---------------------------------------------------------------------------
# SECTION 3: SORTING AND DISPLAYING THE STORIES
# ---------------------------------------------------------------------------
# Here we filter and organize the results so the most appreciated community
# discussions appear right at the top.
# ---------------------------------------------------------------------------
def display_top_stories(hits, topic: str):
    """
    Sorts stories by upvote points in descending order and prints the top results.
    """
    if not hits:
        print(f"\nNo recent stories found for '{topic}' in the last {DAYS_BACK} days.")
        print("Tip: You can try broader keywords (for example: 'AI' instead of a very long phrase).")
        return

    # Sort stories by points (upvotes) in descending order.
    # If points is None or missing, we treat it safely as 0.
    sorted_hits = sorted(hits, key=lambda story: story.get("points") or 0, reverse=True)

    # Slice out our top stories
    top_stories = sorted_hits[:TOP_STORIES_TO_SHOW]

    print("\n" + "=" * 64)
    print(f" Top {len(top_stories)} Hacker News Stories for '{topic}'")
    print(f" (From the past {DAYS_BACK} days, ranked by community upvotes)")
    print("=" * 64 + "\n")

    for index, story in enumerate(top_stories, start=1):
        title = story.get("title") or "Untitled Post"
        points = story.get("points") or 0
        comments = story.get("num_comments") or 0
        
        # Link to the original article or discussion
        item_id = story.get("objectID")
        hn_discussion_url = f"https://news.ycombinator.com/item?id={item_id}"
        story_url = story.get("url") or hn_discussion_url

        print(f"[{index}] {title}")
        print(f"    * Upvotes:     {points}")
        print(f"    * Comments:    {comments}")
        print(f"    * Story URL:   {story_url}")
        if story_url != hn_discussion_url:
            print(f"    * Discussion:  {hn_discussion_url}")
        print("-" * 64)


# ---------------------------------------------------------------------------
# SECTION 4: MAIN PROGRAM RUNNER
# ---------------------------------------------------------------------------
# This handles reading command-line arguments or prompting the user.
# ---------------------------------------------------------------------------
def main():
    # If the user passed arguments in terminal, join them as the search topic
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:]).strip()
    else:
        # Otherwise, ask the user interactively
        try:
            topic = input("What topic would you like to explore from the last 30 days? ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Have a great day!")
            return

    if not topic:
        print("Please provide a topic to search for.")
        return

    print(f"\nSearching Hacker News for community stories about '{topic}'...")
    hits = search_hacker_news(topic)
    display_top_stories(hits, topic)


if __name__ == "__main__":
    main()
