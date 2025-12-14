import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from bot import MastodonRSSBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration loaded from environment variables."""

    instance_url: str
    client_id: str
    client_secret: str
    access_token: str
    feed_urls: List[str] = field(default_factory=list)
    toot_visibility: str = "public"
    check_interval: int = 300
    state_file: Path = field(
        default_factory=lambda: Path("/state/processed_entries.txt")
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        instance_url = os.environ.get("MASTODON_INSTANCE_URL")
        client_id = os.environ.get("MASTODON_CLIENT_ID")
        client_secret = os.environ.get("MASTODON_CLIENT_SECRET")
        access_token = os.environ.get("MASTODON_ACCESS_TOKEN")

        if not all([instance_url, client_id, client_secret, access_token]):
            missing = [
                k
                for k, v in {
                    "MASTODON_INSTANCE_URL": instance_url,
                    "MASTODON_CLIENT_ID": client_id,
                    "MASTODON_CLIENT_SECRET": client_secret,
                    "MASTODON_ACCESS_TOKEN": access_token,
                }.items()
                if not v
            ]
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        # Parse feeds
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
        if feeds_file:
            path = Path(feeds_file)
            if path.exists():
                try:
                    content = path.read_text().splitlines()
                    file_feeds = [
                        line.strip()
                        for line in content
                        if line.strip() and not line.startswith("#")
                    ]
                    feed_urls.extend(file_feeds)
                except Exception as e:
                    logger.error(f"Error reading feeds file {feeds_file}: {e}")
            else:
                logger.warning(f"Feeds file configured but not found: {feeds_file}")

        # Deduplicate while preserving order
        unique_feed_urls = list(dict.fromkeys(feed_urls))

        if not unique_feed_urls:
            raise ValueError(
                "No RSS feeds configured. Please set RSS_FEED_URL, RSS_FEEDS, or FEEDS_FILE."
            )

        return cls(
            instance_url=instance_url,  # type: ignore # checked above
            client_id=client_id,  # type: ignore
            client_secret=client_secret,  # type: ignore
            access_token=access_token,  # type: ignore
            feed_urls=unique_feed_urls,
            toot_visibility=os.environ.get("TOOT_VISIBILITY", "public"),
            check_interval=int(os.environ.get("CHECK_INTERVAL", "300")),
            state_file=Path(
                os.environ.get("PROCESSED_ENTRIES_FILE", "/state/processed_entries.txt")
            ),
        )


def main():
    """Initialize and run the bot with environment configuration"""
    logger.info("Starting Mastodon RSS Bot...")

    try:
        config = Config.from_env()
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        sys.exit(1)

    logger.info("Bot configured successfully:")
    logger.info(f"  Instance: {config.instance_url}")
    logger.info(f"  Monitoring {len(config.feed_urls)} feed(s):")
    for url in config.feed_urls:
        logger.info(f"    - {url}")
    logger.info(f"  Visibility: {config.toot_visibility}")
    logger.info(f"  Check interval: {config.check_interval} seconds")
    logger.info(f"  State file: {config.state_file}")

    bot = MastodonRSSBot(
        client_id=config.client_id,
        client_secret=config.client_secret,
        access_token=config.access_token,
        instance_url=config.instance_url,
        feed_urls=config.feed_urls,
        toot_visibility=config.toot_visibility,
        check_interval=config.check_interval,
        state_file=config.state_file,
    )

    # Start the bot
    bot.run()


if __name__ == "__main__":
    main()
