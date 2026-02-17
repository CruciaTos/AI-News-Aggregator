#!/usr/bin/env python3
"""Simple CLI to fetch recent RSS entries and save to JSON.

Usage:
  python scripts/fetch_rss.py --url URL --out recent.json
"""
from __future__ import annotations

import argparse
import json
import sys

from backend.app.ingest import rss


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch recent RSS/Atom entries and save to JSON")
    p.add_argument("--url", action="append", help="Feed URL to fetch (can be repeated)")
    p.add_argument("--hours", type=int, default=24, help="How many hours back to collect (default: 24)")
    p.add_argument("--out", default="recent.json", help="Output JSON file path")
    p.add_argument("--timeout", type=int, default=10, help="HTTP timeout seconds")
    args = p.parse_args()

    urls = args.url or []

    # If no --url provided, accept piped input or interactive pasted links
    if not urls:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            urls = [line.strip() for line in data.splitlines() if line.strip()]
        else:
            print("Paste feed URLs (one per line). End with an empty line:")
            lines = []
            while True:
                try:
                    line = input().strip()
                except EOFError:
                    break
                if line == "":
                    break
                lines.append(line)
            urls = lines

    if not urls:
        print("No URLs provided.", file=sys.stderr)
        return 2

    combined = []
    for url in urls:
        try:
            items = rss.fetch_recent(url, hours=args.hours, timeout=args.timeout)
            combined.extend(items)
            print(f"Fetched {len(items)} items from")
        except Exception as e:
            print(f"Skipped {url}: {e}", file=sys.stderr)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(combined, fh, ensure_ascii=False, indent=2)

    print(f"Wrote {len(combined)} total entries to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
