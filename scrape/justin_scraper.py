"""
LinkedIn post scraper for Justin Shriber.

Production path uses Apify (which has pre-built LinkedIn scrapers with proper
rate-limit handling and anti-bot tooling). Falls back to the cached
data/justin_posts.json file if Apify isn't configured.

LinkedIn scraping has real ToS considerations — Apify is the production-grade
answer because they handle the headless browser, the auth rotation, and the
rate limits as a managed service. For a prototype, the manual JSON cache is
fine.

Usage:
    from scrape.justin_scraper import load_posts

    posts = load_posts()  # uses Apify if configured, falls back to cache
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
CACHE_PATH = ROOT / "data" / "justin_posts.json"
JUSTIN_PROFILE_URL = "https://www.linkedin.com/in/justinshriber/"


def scrape_via_apify(profile_url: str = JUSTIN_PROFILE_URL, max_posts: int = 20) -> list[dict]:
    """
    Scrape posts from a LinkedIn profile via Apify's LinkedIn Posts Scraper actor.

    Requires:
        - APIFY_TOKEN in .env
        - apify-client Python package (`pip install apify-client`)

    Returns a list of post dicts matching the schema used in data/justin_posts.json.
    """
    try:
        from apify_client import ApifyClient
    except ImportError:
        raise RuntimeError(
            "apify-client not installed. Run: pip install apify-client"
        )

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError(
            "APIFY_TOKEN not set in .env. Sign up at apify.com for a free token."
        )

    client = ApifyClient(token)

    # Apify actor: "apify/linkedin-posts-scraper" or equivalent.
    # The actor ID is configurable so you can swap to a different community actor.
    actor_id = os.environ.get("APIFY_ACTOR_ID", "apify/linkedin-posts-scraper")

    run_input = {
        "startUrls": [{"url": profile_url}],
        "maxPosts": max_posts,
    }

    print(f"🕷  Running Apify actor {actor_id} on {profile_url}...")
    run = client.actor(actor_id).call(run_input=run_input)

    posts = []
    for idx, item in enumerate(
        client.dataset(run["defaultDatasetId"]).iterate_items(), start=1
    ):
        text = item.get("text") or item.get("content") or ""
        if not text.strip():
            continue  # skip empty / image-only posts

        posts.append({
            "id": f"post_{idx:03d}",
            "date": item.get("postedAt") or item.get("date") or "",
            "url": item.get("postUrl") or item.get("url") or "",
            "text": text.strip(),
            "engagement": {
                "likes": item.get("numLikes") or item.get("likes", 0),
                "comments": item.get("numComments") or item.get("comments", 0),
            },
        })

    print(f"   Scraped {len(posts)} posts")
    return posts


def load_from_cache() -> list[dict]:
    """Load the cached posts from data/justin_posts.json."""
    if not CACHE_PATH.exists():
        raise FileNotFoundError(
            f"Cache file not found: {CACHE_PATH}. "
            "Run scripts/scrape_justin.py first, or create the file manually."
        )
    return json.loads(CACHE_PATH.read_text())


def load_posts(prefer_live_scrape: bool = False) -> list[dict]:
    """
    Load Justin's posts. Tries the live scraper first if Apify is configured
    AND prefer_live_scrape is True; otherwise uses the cached JSON.

    For the pipeline's runtime, we use the cache by default — the scraper is a
    separate manual step that refreshes the cache. This keeps the pipeline
    deterministic and avoids hitting Apify on every pipeline run.
    """
    if prefer_live_scrape and os.environ.get("APIFY_TOKEN"):
        try:
            return scrape_via_apify()
        except Exception as e:
            print(f"⚠️  Live scrape failed: {e}")
            print("   Falling back to cached data.")

    return load_from_cache()


def refresh_cache() -> int:
    """
    Run the live scraper and overwrite data/justin_posts.json with fresh data.
    Returns the number of posts scraped.
    """
    posts = scrape_via_apify()
    CACHE_PATH.write_text(json.dumps(posts, indent=2))
    print(f"✅ Cache refreshed: {len(posts)} posts written to {CACHE_PATH}")
    return len(posts)