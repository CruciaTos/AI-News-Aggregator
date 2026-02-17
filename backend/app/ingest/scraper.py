"""Small web-scraping helpers.

These helpers are intentionally simple and best-effort. They perform
network I/O only when called (no side effects at import time).
"""
from __future__ import annotations

from typing import Optional


def fetch_html(url: str, timeout: int = 10) -> str:
    """Fetch the HTML for `url` and return it as text.

    Raises the underlying `requests` exceptions on network errors.
    """
    import requests

    headers = {"User-Agent": "ai-news-aggregator/1.0 (+https://example.local)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def extract_text(html: str) -> Optional[str]:
    """Extract main article text from `html` using simple heuristics.

    Returns extracted text or `None` if nothing useful was found.
    """
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # Remove scripts/styles
    for s in soup(["script", "style", "noscript"]):
        s.extract()

    # Prefer <article>
    article = soup.find("article")
    if article:
        text = article.get_text(separator=" ", strip=True)
        if text:
            return text

    # Try role=main or id=main
    main = soup.find(attrs={"role": "main"}) or soup.find(id="main")
    if main:
        text = main.get_text(separator=" ", strip=True)
        if text:
            return text

    # Fallback: join all <p> elements (common heuristic)
    ps = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    if ps:
        joined = "\n\n".join(ps).strip()
        return joined or None

    return None

