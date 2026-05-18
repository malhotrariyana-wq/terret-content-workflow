"""
CLI script to run the LinkedIn scraper and refresh data/justin_posts.json.

Run from the repo root:
    python -m scripts.scrape_justin

Requires APIFY_TOKEN in .env.
"""

from scrape.justin_scraper import refresh_cache


if __name__ == "__main__":
    count = refresh_cache()
    print(f"\nDone. {count} posts available in data/justin_posts.json")
    print("You can now run: python -m generate.pipeline")