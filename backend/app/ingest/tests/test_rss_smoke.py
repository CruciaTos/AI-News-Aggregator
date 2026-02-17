"""Smoke tests for RSS parsing utilities without network access."""
from __future__ import annotations

import feedparser

from backend.app.ingest import rss


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Test Feed</title>
<link>http://example.com/</link>
<description>Example</description>
<item>
  <title>Item One</title>
  <link>http://example.com/1</link>
  <guid>1</guid>
  <pubDate>Tue, 17 Feb 2026 10:00:00 GMT</pubDate>
  <description><![CDATA[<p>Hello <b>world</b></p>]]></description>
</item>
</channel>
</rss>
"""


def test_parse_entries_basic():
    feed = feedparser.parse(SAMPLE_FEED)
    entries = feed.entries
    normalized = rss.parse_entries(entries, feed_title=feed.feed.get("title"))

    assert isinstance(normalized, list)
    assert len(normalized) == 1

    item = normalized[0]
    assert item["title"] == "Item One"
    assert item["link"] == "http://example.com/1"
    assert "Hello world" in item["summary"] or "Hello" in item["summary"]
    assert "published" in item
