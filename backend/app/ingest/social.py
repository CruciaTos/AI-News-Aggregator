"""Social-platform scrapers for Reddit and X (Twitter).

These are best-effort scrapers that return normalized dicts similar to
the RSS parser output so the local LLM pipeline can consume them.

Notes:
- Reddit: uses the public JSON endpoints at `https://www.reddit.com/r/{subreddit}/.json`.
- X/Twitter: uses the public oEmbed endpoint `https://publish.twitter.com/oembed`
  to extract embed HTML and author info (no API key required).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import re
import json
from typing import Iterable

from backend.app.ingest import rss
from backend.app.ingest import scraper


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_reddit_subreddit(subreddit: str, limit: int = 25, timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent posts from a subreddit using Reddit's JSON endpoint.

    Example: `subreddit='news'` will fetch from `https://www.reddit.com/r/news/new.json`.
    """
    import requests

    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {"User-Agent": "ai-news-aggregator (+https://example.local)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    out: List[Dict[str, Any]] = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        created = datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat()
        item: Dict[str, Any] = {
            "id": d.get("id"),
            "title": d.get("title") or "",
            "link": f"https://reddit.com{d.get('permalink')}" if d.get("permalink") else d.get("url"),
            "published": created,
            "summary": d.get("selftext") or "",
            "content": d.get("selftext") or "",
            "authors": [d.get("author")] if d.get("author") else [],
            "tags": [d.get("link_flair_text")] if d.get("link_flair_text") else [],
            "source": f"reddit:{subreddit}",
            "fetched_at": _now_iso(),
        }

        # If no selftext and the post is a link, attempt to fetch linked page text
        if not item["content"] and d.get("url"):
            try:
                from backend.app.ingest.scraper import fetch_html, extract_text

                html = fetch_html(d.get("url"), timeout=5)
                text = extract_text(html) or ""
                if text:
                    item["content"] = text
            except Exception:
                pass

        out.append(item)

    return out


def fetch_reddit_post(post_url: str, timeout: int = 8) -> List[Dict[str, Any]]:
    """Fetch a single Reddit post given its URL and return a list with one normalized item.

    The function will request the JSON form of the post (`.json`) and normalize the first
    post it finds. Returns an empty list on failure.
    """
    import requests

    if not post_url.endswith(".json"):
        if post_url.endswith("/"):
            post_url = post_url[:-1]
        post_url = post_url + ".json"

    headers = {"User-Agent": "ai-news-aggregator (+https://example.local)"}
    try:
        resp = requests.get(post_url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    try:
        # Reddit post JSON can be a list where the first element contains post data
        post_data = None
        if isinstance(data, list) and data:
            post_list = data[0].get("data", {}).get("children", [])
            if post_list:
                post_data = post_list[0].get("data", {})
        elif isinstance(data, dict):
            # Some endpoints return a dict
            post_list = data.get("data", {}).get("children", [])
            if post_list:
                post_data = post_list[0].get("data", {})

        if not post_data:
            return []

        created = datetime.fromtimestamp(post_data.get("created_utc", 0), tz=timezone.utc).isoformat()
        item: Dict[str, Any] = {
            "id": post_data.get("id"),
            "title": post_data.get("title") or "",
            "link": f"https://reddit.com{post_data.get('permalink')}" if post_data.get("permalink") else post_data.get("url"),
            "published": created,
            "summary": post_data.get("selftext") or "",
            "content": post_data.get("selftext") or "",
            "authors": [post_data.get("author")] if post_data.get("author") else [],
            "tags": [post_data.get("link_flair_text")] if post_data.get("link_flair_text") else [],
            "source": f"reddit:post",
            "fetched_at": _now_iso(),
        }

        # Try to fetch linked page text if no selftext
        if not item["content"] and post_data.get("url"):
            try:
                from backend.app.ingest.scraper import fetch_html, extract_text

                html = fetch_html(post_data.get("url"), timeout=5)
                text = extract_text(html) or ""
                if text:
                    item["content"] = text
            except Exception:
                pass

        out.append(item)
    except Exception:
        return []

    return out


def fetch_x_oembed(tweet_url: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    """Fetch tweet info using Twitter's publish oEmbed endpoint.

    Returns a normalized dict or None on failure.
    """
    import requests
    from bs4 import BeautifulSoup

    oembed_url = "https://publish.twitter.com/oembed"
    headers = {"User-Agent": "ai-news-aggregator (+https://example.local)"}
    resp = requests.get(oembed_url, params={"url": tweet_url}, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    html = data.get("html", "")
    author_name = data.get("author_name")
    author_url = data.get("author_url")

    # Extract text from the returned embed HTML
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(separator=" ", strip=True)

    item = {
        "id": None,
        "title": text[:120],
        "link": tweet_url,
        "published": None,
        "summary": text,
        "content": text,
        "authors": [author_name] if author_name else ([] if not author_url else [author_url]),
        "tags": [],
        "source": "x",
        "fetched_at": _now_iso(),
    }

    return item


def fetch_x_status(tweet_url: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    """Wrapper to fetch a tweet and normalize it; returns dict or None."""
    try:
        return fetch_x_oembed(tweet_url, timeout=timeout)
    except Exception:
        return None


def process_url_list(urls: Iterable[str], out: str = "recent.json", hours: int = 24, timeout: int = 10) -> int:
    """Dispatch a list of URLs to the appropriate social/rss scrapers and write combined JSON.

    The function accepts mixed URLs: subreddit pages, reddit post URLs, twitter/x status URLs,
    or regular RSS/HTML pages. It will try social scrapers first for known hosts, otherwise
    fall back to RSS resolution and finally raw HTML extraction.
    """
    items = collect_from_urls(urls, hours=hours, timeout=timeout)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=2)

    print(f"Wrote {len(items)} total entries to {out}")
    return len(items)


def collect_from_urls(urls: Iterable[str], hours: int = 24, timeout: int = 10) -> List[Dict[str, Any]]:
    """Collect normalized items from a list of URLs and return the combined list.

    This is the programmatic core used by `process_url_list` and callers that
    want the items in-memory instead of writing to disk.
    """
    combined: List[Dict[str, Any]] = []
    urls = list(urls)
    total = len(urls)
    print(f"Processing {total} source(s)...")
    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{total}] {url}")
        try:
            items: List[Dict[str, Any]] = []
            lower = url.lower()

            # Reddit subreddit vs post
            if "reddit.com" in lower or "redd.it" in lower or lower.startswith("r/"):
                if "/comments/" in lower:
                    try:
                        res = fetch_reddit_post(url, timeout=timeout)
                    except NameError:
                        res = []
                    if isinstance(res, dict):
                        items = [res]
                    else:
                        items = list(res or [])
                else:
                    m = re.search(r"reddit\.com/r/([^/]+)/?", lower)
                    if m:
                        subreddit = m.group(1)
                        try:
                            items = fetch_reddit_subreddit(subreddit, limit=25, timeout=timeout)
                        except TypeError:
                            items = fetch_reddit_subreddit(subreddit, limit=25)

            # Twitter / X single status
            elif "twitter.com" in lower or "x.com" in lower:
                try:
                    item = fetch_x_status(url, timeout=timeout)
                    if item:
                        items = [item]
                except Exception as e:
                    print(f"  failed x/twitter: {e}")

            else:
                # Fallback: try RSS/Atom resolution
                try:
                    items = rss.fetch_recent(url, hours=hours, timeout=timeout)
                except Exception:
                    # As a last resort, fetch the html and extract text
                    try:
                        html = scraper.fetch_html(url, timeout=timeout)
                        text = scraper.extract_text(html)
                        if text:
                            now = datetime.now(timezone.utc).isoformat()
                            items = [{
                                "id": url,
                                "title": None,
                                "link": url,
                                "published": now,
                                "summary": None,
                                "content": text,
                                "authors": [],
                                "tags": [],
                                "source": url,
                                "fetched_at": now,
                            }]
                    except Exception as e:
                        print(f"  fallback failed: {e}")

            combined.extend(items or [])
            print(f"  fetched {len(items or [])} items")
        except Exception as e:
            print(f"  skipped {url}: {e}")

    return combined
