"""Mastodon RSS Bot - Core functionality"""

import logging
import time
from pathlib import Path
import random
from typing import List, Optional, Set

import feedparser
from mastodon import Mastodon

# Configure logging for this module
logger = logging.getLogger(__name__)


class MastodonRSSBot:
    """Bot that monitors RSS feeds and posts updates to Mastodon"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        instance_url: str,
        feed_urls: List[str],
        toot_visibility: str = "public",
        check_interval: int = 300,
        notification_check_interval: int = 60,
        state_file: Path = Path("/state/processed_entries.txt"),
        messages_file: Path = Path("sarcastic_messages.txt"),
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
            notification_check_interval: Seconds between notification checks
            state_file: Path to file storing processed entry URLs
            messages_file: Path to file storing sarcastic messages
        """
        self.feed_urls = feed_urls
        self.toot_visibility = toot_visibility
        self.check_interval = check_interval
        self.notification_check_interval = notification_check_interval
        self.state_file = Path(state_file)
        self.messages_file = Path(messages_file)

        # Load sarcastic messages
        self.sarcastic_messages = self.load_sarcastic_messages()

        # State for notification tracking
        self.last_notification_id = None

        # Initialize Mastodon client
        self.mastodon = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            api_base_url=instance_url,
        )

    def load_sarcastic_messages(self) -> List[str]:
        """
        Load sarcastic messages from the configured file.
        Favorites fallback if file is missing.
        """
        if not self.messages_file.exists():
            logger.warning(f"Messages file {self.messages_file} not found. Using defaults.")
            return ["I am a bot. Beep boop."]

        try:
            messages = [line.strip() for line in self.messages_file.read_text().splitlines() if line.strip()]
            logger.info(f"Loaded {len(messages)} sarcastic messages.")
            return messages
        except Exception as e:
            logger.error(f"Error loading messages: {e}")
            return ["I am a bot. Beep boop."]

    def load_processed_entries(self) -> Set[str]:
        """
        Load the set of processed entry URLs from the state file.

        Returns:
            Set of URLs that have been processed
        """
        if not self.state_file.exists():
            return set()

        try:
            return set(self.state_file.read_text().splitlines())
        except Exception as e:
            logger.error(f"Error loading processed entries from {self.state_file}: {e}")
            return set()

    def save_processed_entries(self, processed_entries: Set[str]) -> None:
        """
        Save the set of processed entry URLs to the state file.

        Args:
            processed_entries: Set of processed entry URLs
        """
        # Ensure directory exists
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text("\n".join(sorted(processed_entries)))
        except Exception as e:
            logger.error(f"Error saving processed entries to {self.state_file}: {e}")

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
                logger.warning(f"Feed parsing issue for {feed_url}: {feed.bozo_exception}")
            return feed
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
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
            logger.error(f"Error posting to Mastodon: {e}")
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
        logger.info(f"Checking feed: {feed_url}")
        feed = self.parse_feed(feed_url)
        if not feed or not hasattr(feed, "entries"):
            logger.warning(f"No entries found in feed: {feed_url}")
            return 0

        new_entries_count = 0

        # Process each entry
        for entry in feed.entries:
            entry_url = entry.get("link", "")

            if not entry_url:
                logger.debug("Skipping entry without URL")
                continue

            # Check if entry is new
            if entry_url not in processed_entries:
                title = entry.get("title", "Untitled")
                logger.info(f"Found a new RSS item: {title}")

                # Format and post status
                status = self.format_status(entry)
                if self.post_to_mastodon(status):
                    processed_entries.add(entry_url)
                    new_entries_count += 1
                else:
                    logger.error(f"Failed to post entry: {title}")

        return new_entries_count

    def process_new_entries(self) -> int:
        """
        Check for new feed entries in all feeds and post them to Mastodon.

        Returns:
            Total number of new entries posted across all feeds
        """
        logger.info("Checking for new RSS items...")

        # Load processed entries
        processed_entries = self.load_processed_entries()

        total_new_entries = 0

        for feed_url in self.feed_urls:
            total_new_entries += self.process_feed(feed_url, processed_entries)

        # Save updated state
        if total_new_entries > 0:
            self.save_processed_entries(processed_entries)

        return total_new_entries

    def check_notifications(self) -> None:
        """
        Check for mentions and reply with sarcasm.
        """
        try:
            # First run, just get the latest ID so we don't reply to old stuff if we restart
            if self.last_notification_id is None:
                notes = self.mastodon.notifications(types=['mention'], limit=1)
                if notes:
                    self.last_notification_id = notes[0]['id']
                else:
                    self.last_notification_id = 0 # Start from beginning if no notes
                return

            notifications = self.mastodon.notifications(
                types=['mention'],
                since_id=self.last_notification_id
            )

            for note in notifications:
                self.last_notification_id = max(self.last_notification_id, note['id'])
                self.reply_to_mention(note)

                # Dismiss notification so we don't see it again in UI (optional, but clean)
                try:
                    self.mastodon.notifications_dismiss(note['id'])
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error checking notifications: {e}")

    def reply_to_mention(self, notification) -> None:
        """
        Reply to a mention with a random sarcastic message.
        """
        status = notification.get('status')
        if not status:
            return

        account = status.get('account')
        if not account:
            return

        username = account.get('acct')
        mention_text = f"@{username} {random.choice(self.sarcastic_messages)}"

        logger.info(f"Responding to {username} with sarcasm.")

        try:
            self.mastodon.status_post(
                mention_text,
                in_reply_to_id=status['id'],
                visibility=self.toot_visibility
            )
        except Exception as e:
            logger.error(f"Failed to reply to {username}: {e}")

    def run(self) -> None:
        """
        Main loop: continuously monitor the feed and post new entries,
        plus check for notifications.
        """
        logger.info("Bot starting up...")

        next_feed_check = 0
        next_notification_check = 0

        while True:
            try:
                current_time = time.time()

                # Check feeds
                if current_time >= next_feed_check:
                    count = self.process_new_entries()
                    if count > 0:
                        logger.info(f"Posted {count} new entries")
                    next_feed_check = current_time + self.check_interval

                # Check notifications
                if current_time >= next_notification_check:
                    self.check_notifications()
                    next_notification_check = current_time + self.notification_check_interval

                # Sleep a short time to prevent tight loop
                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5) # Back off on error
