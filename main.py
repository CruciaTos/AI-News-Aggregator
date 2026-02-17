def main():
    # Run RSS and social scrapers in sync and write a combined JSON file.
    try:
        import json
        from scripts import url_links

        # Import scraper modules inside function to avoid network work at import time
        from backend.app.ingest import rss as rss_module
        from backend.app.ingest import social as social_module

        combined = []

        # Use the runner in scripts.url_links which reads WEB_FEEDS and REDDIT_COMMUNITIES
        try:
            count = url_links.run_default(out="combined_recent.json", hours=24)
            print(f"run_default wrote {count} items to combined_recent.json")
        except Exception as e:
            print("Failed running url_links.run_default:", e)
        # (Optional) You can add X/Twitter URLs to fetch via oEmbed in url_links.DEFAULT lists.

    except Exception as exc:
        print("Hello from ai-news-aggregator! (fallback)")
        print("Error while running scrapers:", exc)


if __name__ == "__main__":
    main()
