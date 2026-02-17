"""RSS ingestion utilities.

This module provides small helpers to fetch an RSS/Atom feed and convert
entries into a normalized format suitable for downstream summarization
by a local LLM. Entries without a published date are ignored.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import calendar
from typing import Iterable, List, Dict, Any, Optional
from urllib.parse import urljoin

import feedparser
from bs4 import BeautifulSoup


def _struct_time_to_dt(st):
    if st is None:
        return None
    # Use calendar.timegm to convert a UTC struct_time to a timestamp
    try:
        ts = calendar.timegm(st)
    except Exception:
        # Fallback: convert via time.mktime (may use local tz)
        import time

        ts = time.mktime(st)
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def fetch_feed(url: str, timeout: int = 10) -> feedparser.FeedParserDict:
    """Fetch and parse a feed from `url`.

    Returns the feedparser-parsed object. Network errors raise an
    exception from `requests` (caller may catch them and treat as
    "not available").
    """
    import requests

    headers = {"User-Agent": "ai-news-aggregator/1.0 (+https://example.local)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    parsed = feedparser.parse(resp.content)

    # If response already looks like a feed, return it
    if parsed.entries:
        return parsed

    # If the content-type indicates XML/Feed, return parsed anyway
    if "xml" in content_type or "rss" in content_type or "atom" in content_type:
        return parsed

    # Otherwise, try to resolve an alternate feed link from the HTML page
    feed_url = _resolve_feed_url_from_html(url, resp.content)
    if feed_url:
        resp2 = requests.get(feed_url, headers=headers, timeout=timeout)
        resp2.raise_for_status()
        return feedparser.parse(resp2.content)

    # Fallback: return the original parsed result (may be empty)
    return parsed


def _resolve_feed_url_from_html(base_url: str, html_content: bytes) -> Optional[str]:
    """Inspect `html_content` for feed links and return the first resolved URL.

    Looks for <link rel="alternate" type="application/rss+xml"> and also
    heuristically for anchors containing 'rss' or 'feed' in their href.
    """
    try:
        soup = BeautifulSoup(html_content, "lxml")
    except Exception:
        soup = BeautifulSoup(html_content, "html.parser")

    # Look for <link rel="alternate" ...>
    for link in soup.find_all("link", rel=True):
        rel = link.get("rel")
        # rel may be a list
        if isinstance(rel, (list, tuple)):
            rel = " ".join(rel)
        if "alternate" in (rel or ""):
            ltype = (link.get("type") or "").lower()
            if "rss" in ltype or "xml" in ltype or "atom" in ltype:
                href = link.get("href")
                if href:
                    return urljoin(base_url, href)

    # Heuristic: look for <a href> containing rss/feed/atom
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(tok in href.lower() for tok in ("rss", "feed", "atom")):
            candidates.append(urljoin(base_url, href))

    return candidates[0] if candidates else None


def _fetch_article_content(url: str, timeout: int = 8) -> tuple[str | None, list[str]]:
    """Fetch an article page and attempt to extract the main text and authors.

    Returns (text, authors). Either may be empty/None on failure.
    Uses simple heuristics: <article> tag, role="main", or the largest
    block of consecutive <p> elements.
    """
    import requests

    headers = {"User-Agent": "ai-news-aggregator/1.0 (+https://example.local)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    try:
        soup = BeautifulSoup(resp.content, "lxml")
    except Exception:
        soup = BeautifulSoup(resp.content, "html.parser")

    # remove script/style
    for s in soup(["script", "style", "noscript"]):
        s.extract()

    # Try to find an article tag first
    article = soup.find("article")
    if article:
        text = article.get_text(separator=" ", strip=True)
    else:
        # Try role="main"
        main = soup.find(attrs={"role": "main"}) or soup.find(id="main")
        if main:
            text = main.get_text(separator=" ", strip=True)
        else:
            # Heuristic: find the longest sequence of <p> text
            p_blocks = [" ".join(p.get_text(separator=" ", strip=True) for p in block) for block in []]
            # Simpler: gather all <p> and return the joined text
            ps = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
            text = "\n\n".join(ps).strip()

    # Author heuristics: meta tags or common class names
    authors: list[str] = []
    # meta name=author
    ma = soup.find("meta", attrs={"name": "author"})
    if ma and ma.get("content"):
        authors.append(ma.get("content").strip())

    # meta property article:author or og:article:author
    for prop in ("article:author", "og:article:author", "og:author"):
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            authors.append(tag.get("content").strip())

    # rel=author
    rel = soup.find(attrs={"rel": "author"})
    if rel and rel.get_text(strip=True):
        authors.append(rel.get_text(strip=True))

    # common class/id selectors (best-effort)
    if not authors:
        selectors = [".byline__name", ".author", ".byline", "#byline"]
        for sel in selectors:
            node = soup.select_one(sel)
            if node and node.get_text(strip=True):
                authors.append(node.get_text(strip=True))
                break

    # Deduplicate authors
    authors = [a for i, a in enumerate(authors) if a and a not in authors[:i]]

    return (text if text else None, authors)


def parse_entries(entries: Iterable[Any], feed_title: Optional[str] = None) -> List[Dict[str, Any]]:
    """Normalize feed entries into a list of dicts.

    - Skips entries without a published date.
    - Converts dates to ISO-8601 UTC strings.
    - Cleans HTML from summaries/content using BeautifulSoup.
    """
    out: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for e in entries:
        published_dt = None
        if hasattr(e, "published_parsed") and e.published_parsed:
            published_dt = _struct_time_to_dt(e.published_parsed)
        elif hasattr(e, "updated_parsed") and e.updated_parsed:
            published_dt = _struct_time_to_dt(e.updated_parsed)

        # Ignore entries without a reliable published/updated timestamp
        if not published_dt:
            continue

        # Extract text from summary/content
        summary_html = getattr(e, "summary", None) or ""
        content_text = ""
        if hasattr(e, "content") and e.content:
            # feedparser content is a list of dicts with 'value'
            first = e.content[0]
            content_html = first.get("value") if isinstance(first, dict) else str(first)
            content_text = BeautifulSoup(content_html, "lxml").get_text(separator=" ", strip=True)

        summary_text = BeautifulSoup(summary_html, "lxml").get_text(separator=" ", strip=True)

        authors = []
        if hasattr(e, "author") and e.author:
            authors = [e.author]
        elif hasattr(e, "authors") and e.authors:
            try:
                authors = [a.name for a in e.authors if getattr(a, "name", None)]
            except Exception:
                authors = [str(a) for a in e.authors]

        tags = []
        if hasattr(e, "tags") and e.tags:
            try:
                tags = [t.term for t in e.tags if getattr(t, "term", None)]
            except Exception:
                tags = [str(t) for t in e.tags]

        normalized: Dict[str, Any] = {
            "id": getattr(e, "id", getattr(e, "guid", None) or getattr(e, "link", None)),
            "title": getattr(e, "title", ""),
            "link": getattr(e, "link", None),
            "published": published_dt.isoformat(),
            "summary": summary_text,
            "content": content_text,
            "authors": authors,
            "tags": tags,
            "source": feed_title,
            "fetched_at": now.isoformat(),
        }
        # If no content found in the feed entry, try to fetch the article page
        if not content_text and normalized.get("link"):
            try:
                article_text, page_authors = _fetch_article_content(normalized["link"])
                if article_text:
                    normalized["content"] = article_text
                if not authors and page_authors:
                    normalized["authors"] = page_authors
            except Exception:
                # If article fetch fails, continue without raising
                pass

        out.append(normalized)

    return out


def fetch_recent(url: str, hours: int = 24, timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetch `url` and return normalized entries published in the last `hours` hours.

    If the feed is unavailable an exception from `requests` will be raised.
    Caller can catch exceptions and treat them as "not available".
    """
    feed = fetch_feed(url, timeout=timeout)
    feed_title = feed.feed.get("title") if getattr(feed, "feed", None) else None

    entries = feed.entries if hasattr(feed, "entries") else []
    normalized = parse_entries(entries, feed_title=feed_title)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = [e for e in normalized if datetime.fromisoformat(e["published"]) >= cutoff]
    return recent

