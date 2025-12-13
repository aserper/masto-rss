"""Mastodon RSS Bot - Core functionality"""

import feedparser
from mastodon import Mastodon
import os
import time
from typing import Set, Optional


class MastodonRSSBot:
    """Bot that monitors RSS feeds and posts updates to Mastodon"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        instance_url: str,
        feed_urls: list[str],
        toot_visibility: str = "public",
        check_interval: int = 300,
        state_file: str = "/state/processed_entries.txt",
    ):
        """
        Initialize the Mastodon RSS bot.

        Args:
            client_id: Mastodon application client ID
            client_secret: Mastodon application client secret
            access_token: Mastodon access token
            instance_url: URL of the Mastodon instance
            feed_urls: List of URLs of the RSS/Atom feeds to monitor
            toot_visibility: Visibility level for posts ('public', 'unlisted', 'private', 'direct')
            check_interval: Seconds between feed checks
            state_file: Path to file storing processed entry URLs
        """
        self.feed_urls = feed_urls
        self.toot_visibility = toot_visibility
        self.check_interval = check_interval
        self.state_file = state_file

        # Initialize Mastodon client
        self.mastodon = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            api_base_url=instance_url,
        )

    def load_processed_entries(self) -> Set[str]:
        """
        Load the set of processed entry URLs from the state file.

        Returns:
            Set of URLs that have been processed
        """
        try:
            with open(self.state_file, "r") as file:
                return set(file.read().splitlines())
        except FileNotFoundError:
            return set()

    def save_processed_entries(self, processed_entries: Set[str]) -> None:
        """
        Save the set of processed entry URLs to the state file.

        Args:
            processed_entries: Set of processed entry URLs
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

        with open(self.state_file, "w") as file:
            file.write("\n".join(sorted(processed_entries)))

    def parse_feed(self, feed_url: str) -> Optional[feedparser.FeedParserDict]:
        """
        Parse the RSS feed.

        Args:
            feed_url: URL of the feed to parse

        Returns:
            Parsed feed object or None if parsing fails
        """
        try:
            feed = feedparser.parse(feed_url)
            if hasattr(feed, "bozo_exception"):
                print(
                    f"Warning: Feed parsing issue for {feed_url}: {feed.bozo_exception}"
                )
            return feed
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
            return None

    def format_status(self, entry: feedparser.FeedParserDict) -> str:
        """
        Format a feed entry as a Mastodon status.

        Args:
            entry: Feed entry from feedparser

        Returns:
            Formatted status text
        """
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")
        return f"\n{title}\n\n{link}"

    def post_to_mastodon(self, status: str) -> bool:
        """
        Post a status to Mastodon.

        Args:
            status: Status text to post

        Returns:
            True if successful, False otherwise
        """
        try:
            self.mastodon.status_post(status, visibility=self.toot_visibility)
            return True
        except Exception as e:
            print(f"Error posting to Mastodon: {e}")
            return False

    def process_feed(self, feed_url: str, processed_entries: Set[str]) -> int:
        """
        Process a single feed for new entries.

        Args:
            feed_url: URL of the feed to process
            processed_entries: Set of already processed entry URLs

        Returns:
            Number of new entries posted
        """
        print(f"Checking feed: {feed_url}")
        feed = self.parse_feed(feed_url)
        if not feed or not hasattr(feed, "entries"):
            print(f"No entries found in feed: {feed_url}")
            return 0

        new_entries_count = 0

        # Process each entry
        for entry in feed.entries:
            entry_url = entry.get("link", "")

            if not entry_url:
                print("Skipping entry without URL")
                continue

            # Check if entry is new
            if entry_url not in processed_entries:
                title = entry.get("title", "Untitled")
                print(f"Found a new RSS item: {title}")

                # Format and post status
                status = self.format_status(entry)
                if self.post_to_mastodon(status):
                    processed_entries.add(entry_url)
                    new_entries_count += 1
                else:
                    print(f"Failed to post entry: {title}")

        return new_entries_count

    def process_new_entries(self) -> int:
        """
        Check for new feed entries in all feeds and post them to Mastodon.

        Returns:
            Total number of new entries posted across all feeds
        """
        print("Checking for new RSS items...")

        # Load processed entries
        processed_entries = self.load_processed_entries()

        total_new_entries = 0

        for feed_url in self.feed_urls:
            total_new_entries += self.process_feed(feed_url, processed_entries)

        # Save updated state
        if total_new_entries > 0:
            self.save_processed_entries(processed_entries)

        return total_new_entries

    def run(self) -> None:
        """
        Main loop: continuously monitor the feed and post new entries.
        """
        while True:
            try:
                count = self.process_new_entries()
                if count > 0:
                    print(f"Posted {count} new entries")

                print(f"Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\nBot stopped by user")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                print(f"Retrying in {self.check_interval} seconds...")
                time.sleep(self.check_interval)
