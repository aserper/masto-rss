"""Mastodon RSS Bot - Entry point"""

import os
from bot import MastodonRSSBot


def main():
    """Initialize and run the bot with environment configuration"""
    print("Starting Mastodon RSS Bot...")

    # Load configuration from environment variables
    bot = MastodonRSSBot(
        client_id=os.environ["MASTODON_CLIENT_ID"],
        client_secret=os.environ["MASTODON_CLIENT_SECRET"],
        access_token=os.environ["MASTODON_ACCESS_TOKEN"],
        instance_url=os.environ["MASTODON_INSTANCE_URL"],
        feed_url=os.environ["RSS_FEED_URL"],
        toot_visibility=os.environ.get("TOOT_VISIBILITY", "public"),
        check_interval=int(os.environ.get("CHECK_INTERVAL", "300")),
        state_file=os.environ.get(
            "PROCESSED_ENTRIES_FILE", "/state/processed_entries.txt"
        ),
    )

    print(f"Bot configured successfully:")
    print(f"  Instance: {os.environ['MASTODON_INSTANCE_URL']}")
    print(f"  Feed URL: {os.environ['RSS_FEED_URL']}")
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
