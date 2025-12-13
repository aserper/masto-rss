"""Mastodon RSS Bot - Entry point"""

import os
from bot import MastodonRSSBot


def main():
    """Initialize and run the bot with environment configuration"""
    print("Starting Mastodon RSS Bot...")

    # Load configuration from environment variables
    feed_urls = []

    # 1. Legacy single feed URL
    if os.environ.get("RSS_FEED_URL"):
        feed_urls.append(os.environ["RSS_FEED_URL"])

    # 2. Comma-separated list of feeds
    if os.environ.get("RSS_FEEDS"):
        feeds = [
            url.strip() for url in os.environ["RSS_FEEDS"].split(",") if url.strip()
        ]
        feed_urls.extend(feeds)

    # 3. File containing list of feeds
    feeds_file = os.environ.get("FEEDS_FILE")
    if feeds_file and os.path.exists(feeds_file):
        try:
            with open(feeds_file, "r") as f:
                file_feeds = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
                feed_urls.extend(file_feeds)
        except Exception as e:
            print(f"Error reading feeds file {feeds_file}: {e}")

    # Deduplicate while preserving order
    unique_feed_urls = []
    seen = set()
    for url in feed_urls:
        if url not in seen:
            unique_feed_urls.append(url)
            seen.add(url)

    if not unique_feed_urls:
        print(
            "Error: No RSS feeds configured. Please set RSS_FEED_URL, RSS_FEEDS, or FEEDS_FILE."
        )
        return

    bot = MastodonRSSBot(
        client_id=os.environ["MASTODON_CLIENT_ID"],
        client_secret=os.environ["MASTODON_CLIENT_SECRET"],
        access_token=os.environ["MASTODON_ACCESS_TOKEN"],
        instance_url=os.environ["MASTODON_INSTANCE_URL"],
        feed_urls=unique_feed_urls,
        toot_visibility=os.environ.get("TOOT_VISIBILITY", "public"),
        check_interval=int(os.environ.get("CHECK_INTERVAL", "300")),
        state_file=os.environ.get(
            "PROCESSED_ENTRIES_FILE", "/state/processed_entries.txt"
        ),
    )

    print("Bot configured successfully:")
    print(f"  Instance: {os.environ['MASTODON_INSTANCE_URL']}")
    print(f"  Monitoring {len(unique_feed_urls)} feed(s):")
    for url in unique_feed_urls:
        print(f"    - {url}")
    print(f"  Visibility: {os.environ.get('TOOT_VISIBILITY', 'public')}")
    print(f"  Check interval: {os.environ.get('CHECK_INTERVAL', '300')} seconds")
    print(
        f"  State file: {os.environ.get('PROCESSED_ENTRIES_FILE', '/state/processed_entries.txt')}"
    )
    print()

    # Start the bot
    bot.run()


if __name__ == "__main__":
    main()
