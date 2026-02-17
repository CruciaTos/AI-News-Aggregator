"""Helpers to paste or provide multiple feed URLs and run the RSS scraper.

This module exposes:
- `process_urls(urls, out, hours, timeout)` — process a list of URLs and write combined JSON.
- `run_from_pasted_text(pasted_text, out, hours, timeout)` — split pasted text into URLs and run.
- `paste_and_run()` — interactive prompt for pasting links, then runs the scraper.
"""
from __future__ import annotations

import json
from typing import Iterable, List

from backend.app.ingest import social

# Two separate lists: web feeds (RSS/HTML) and reddit community links
WEB_FEEDS = [
    "https://www.bbc.com/news/science_and_environment",
]

REDDIT_COMMUNITIES = [
    "https://www.reddit.com/r/science/",
    "https://www.reddit.com/r/space/",
    # Add subreddit community URLs here, one per line
]


def run_default(out: str = "recent.json", hours: int = 24, timeout: int = 10) -> int:
    """Run scrapers for `WEB_FEEDS` and `REDDIT_COMMUNITIES` and write combined output."""
    combined = []

    if WEB_FEEDS:
        try:
            items = social.collect_from_urls(WEB_FEEDS, hours=hours, timeout=timeout)
            combined.extend(items)
            print(f"Collected {len(items)} items from WEB_FEEDS")
        except Exception as e:
            print("Failed collecting WEB_FEEDS:", e)

    if REDDIT_COMMUNITIES:
        try:
            items = social.collect_from_urls(REDDIT_COMMUNITIES, hours=hours, timeout=timeout)
            combined.extend(items)
            print(f"Collected {len(items)} items from REDDIT_COMMUNITIES")
        except Exception as e:
            print("Failed collecting REDDIT_COMMUNITIES:", e)

    # write combined output
    import json

    with open(out, "w", encoding="utf-8") as fh:
        json.dump(combined, fh, ensure_ascii=False, indent=2)

    print(f"Wrote {len(combined)} total entries to {out}")
    return len(combined)


def run_from_pasted_text(pasted_text: str, out: str = "recent.json", hours: int = 24, timeout: int = 10) -> int:
    urls = [line.strip() for line in pasted_text.splitlines() if line.strip()]
    return social.process_url_list(urls, out=out, hours=hours, timeout=timeout)


def paste_and_run(out: str = "recent.json", hours: int = 24, timeout: int = 10) -> int:
    print("Paste feed URLs (one per line). End with an empty line:")
    lines: List[str] = []
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    return social.process_url_list(lines, out=out, hours=hours, timeout=timeout)


if __name__ == "__main__":
    paste_and_run()
