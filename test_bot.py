"""Unit tests for Mastodon RSS Bot"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from pathlib import Path
from bot import MastodonRSSBot


class TestMastodonRSSBot(unittest.TestCase):
    """Test cases for MastodonRSSBot class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "access_token": "test_access_token",
            "instance_url": "https://mastodon.test",
            "feed_urls": ["https://example.com/feed.xml"],
            "toot_visibility": "public",
            "check_interval": 60,
            "notification_check_interval": 30,
            "state_file": tempfile.mktemp(),
            "messages_file": tempfile.mktemp(),
        }

        # Create dummy messages file
        with open(self.test_config["messages_file"], "w") as f:
            f.write("I am a bot.\n")

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_config["state_file"]):
            os.remove(self.test_config["state_file"])
        if os.path.exists(self.test_config["messages_file"]):
            os.remove(self.test_config["messages_file"])

    @patch("bot.Mastodon")
    def test_bot_initialization(self, mock_mastodon):
        """Test bot initializes with correct configuration"""
        bot = MastodonRSSBot(**self.test_config)

        self.assertEqual(bot.feed_urls, self.test_config["feed_urls"])
        self.assertEqual(bot.toot_visibility, self.test_config["toot_visibility"])
        self.assertEqual(bot.check_interval, self.test_config["check_interval"])
        self.assertEqual(bot.notification_check_interval, self.test_config["notification_check_interval"])
        self.assertEqual(bot.state_file, Path(self.test_config["state_file"]))
        self.assertEqual(bot.messages_file, Path(self.test_config["messages_file"]))

        # Verify Mastodon client was initialized correctly
        mock_mastodon.assert_called_once_with(
            client_id=self.test_config["client_id"],
            client_secret=self.test_config["client_secret"],
            access_token=self.test_config["access_token"],
            api_base_url=self.test_config["instance_url"],
        )

    @patch("bot.Mastodon")
    def test_save_processed_entries_error(self, mock_mastodon):
        """Test error handling when saving processed entries fails"""
        bot = MastodonRSSBot(**self.test_config)

        # Mock Path.write_text to raise exception
        with patch.object(Path, "write_text", side_effect=Exception("Disk full")):
            # Should not raise exception
            bot.save_processed_entries({"https://example.com/1"})

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_parse_feed_bozo(self, mock_mastodon, mock_parse):
        """Test feed parsing with bozo exception (warning)"""
        mock_feed = Mock()
        mock_feed.bozo_exception = Exception("XML Error")
        mock_parse.return_value = mock_feed

        bot = MastodonRSSBot(**self.test_config)
        feed = bot.parse_feed("https://example.com/feed.xml")

        self.assertIsNotNone(feed)
        # We can't easily assert the log/print was called without mocking logging,
        # but execution flow is covered.

    @patch("bot.Mastodon")
    def test_run_keyboard_interrupt(self, mock_mastodon):
        """Test clean exit on KeyboardInterrupt"""
        bot = MastodonRSSBot(**self.test_config)

        # Mock process_new_entries to raise KeyboardInterrupt
        bot.process_new_entries = Mock(side_effect=KeyboardInterrupt)

        # Should exit cleanly
        bot.run()
        bot.process_new_entries.assert_called_once()

    @patch("bot.time.sleep")
    @patch("bot.Mastodon")
    def test_run_exception_retry(self, mock_mastodon, mock_sleep):
        """Test retry logic on exception in main loop"""
        bot = MastodonRSSBot(**self.test_config)

        # Raise exception once, then KeyboardInterrupt to exit loop
        bot.process_new_entries = Mock(side_effect=[Exception("Network Error"), KeyboardInterrupt])

        bot.run()

        self.assertEqual(bot.process_new_entries.call_count, 2)
        mock_sleep.assert_called_with(5)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_feed_new_entry(self, mock_mastodon, mock_parse):
        """Test processing feed with a new entry"""
        mock_feed = Mock()
        mock_feed.entries = [{"title": "New", "link": "http://new.com", "description": "desc"}]
        mock_parse.return_value = mock_feed

        # Mock instance
        mock_instance = Mock()
        mock_instance.status_post.return_value = {}
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        processed = set()
        count = bot.process_feed("http://feed.com", processed)

        self.assertEqual(count, 1)
        self.assertIn("http://new.com", processed)
        mock_instance.status_post.assert_called_once()

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_feed_existing_entry(self, mock_mastodon, mock_parse):
        """Test processing feed with existing entry"""
        mock_feed = Mock()
        mock_feed.entries = [{"link": "http://old.com"}]
        mock_parse.return_value = mock_feed

        bot = MastodonRSSBot(**self.test_config)
        processed = {"http://old.com"}
        count = bot.process_feed("http://feed.com", processed)

        self.assertEqual(count, 0)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_feed_post_failure(self, mock_mastodon, mock_parse):
        """Test handling of post failure"""
        mock_feed = Mock()
        mock_feed.entries = [{"link": "http://fail.com"}]
        mock_parse.return_value = mock_feed

        mock_instance = Mock()
        mock_instance.status_post.side_effect = Exception("API Error")
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        processed = set()
        count = bot.process_feed("http://feed.com", processed)

        self.assertEqual(count, 0)
        self.assertNotIn("http://fail.com", processed)

    @patch("bot.Mastodon")
    def test_process_new_entries_delegation(self, mock_mastodon):
        """Test process_new_entries calls process_feed for each URL"""
        bot = MastodonRSSBot(**self.test_config)
        bot.feed_urls = ["http://feed1.com", "http://feed2.com"]

        with (
            patch.object(bot, "load_processed_entries", return_value=set()),
            patch.object(bot, "process_feed", side_effect=[1, 2]) as mock_process,
            patch.object(bot, "save_processed_entries") as mock_save,
        ):
            total = bot.process_new_entries()

            self.assertEqual(total, 3)
            self.assertEqual(mock_process.call_count, 2)
            mock_save.assert_called_once()


class TestMainEntry(unittest.TestCase):
    """Test cases for main.py entry point"""

    @patch.dict(os.environ, {}, clear=True)
    def test_config_missing_vars(self):
        """Test Config raises ValueError when env vars are missing"""
        from main import Config

        with self.assertRaises(ValueError):
            Config.from_env()

    @patch.dict(
        os.environ,
        {
            "MASTODON_CLIENT_ID": "id",
            "MASTODON_CLIENT_SECRET": "secret",
            "MASTODON_ACCESS_TOKEN": "token",
            "MASTODON_INSTANCE_URL": "url",
            # No feed urls
        },
    )
    def test_config_no_feeds(self):
        """Test Config raises ValueError when no feeds are configured"""
        from main import Config

        with self.assertRaises(ValueError):
            Config.from_env()

    @patch.dict(
        os.environ,
        {
            "MASTODON_CLIENT_ID": "id",
            "MASTODON_CLIENT_SECRET": "secret",
            "MASTODON_ACCESS_TOKEN": "token",
            "MASTODON_INSTANCE_URL": "url",
            "FEEDS_FILE": "nonexistent.txt",
        },
    )
    def test_config_feed_file_error(self):
        """Test Config handles missing/bad feeds file gracefully (logs warning but continues check)"""
        from main import Config

        # Should raise ValueError ultimately because no feeds are found,
        # but cover the file reading path
        with self.assertRaises(ValueError) as cm:
            Config.from_env()
        self.assertIn("No RSS feeds configured", str(cm.exception))

    @patch.dict(
        os.environ,
        {
            "MASTODON_CLIENT_ID": "test_id",
            "MASTODON_CLIENT_SECRET": "test_secret",
            "MASTODON_ACCESS_TOKEN": "test_token",
            "MASTODON_INSTANCE_URL": "https://mastodon.test",
            "RSS_FEED_URL": "https://example.com/feed.xml",
            "TOOT_VISIBILITY": "unlisted",
            "CHECK_INTERVAL": "120",
            "PROCESSED_ENTRIES_FILE": "/tmp/test_state.txt",
        },
    )
    @patch("main.MastodonRSSBot")
    def test_main_loads_legacy_environment_config(self, mock_bot_class):
        """Test that main() loads configuration from legacy environment variable"""
        from main import main

        mock_bot_instance = Mock()
        mock_bot_class.return_value = mock_bot_instance

        # Call main (but it will try to run, so we need to handle that)
        try:
            main()
        except Exception:
            pass  # Expected since we're mocking

        # Verify bot was created with correct config
        mock_bot_class.assert_called_once_with(
            client_id="test_id",
            client_secret="test_secret",
            access_token="test_token",
            instance_url="https://mastodon.test",
            feed_urls=["https://example.com/feed.xml"],
            toot_visibility="unlisted",
            check_interval=120,
            notification_check_interval=60,
            state_file=Path("/tmp/test_state.txt"),
            messages_file=Path("sarcastic_messages.txt"),
        )

    @patch.dict(
        os.environ,
        {
            "MASTODON_CLIENT_ID": "test_id",
            "MASTODON_CLIENT_SECRET": "test_secret",
            "MASTODON_ACCESS_TOKEN": "test_token",
            "MASTODON_INSTANCE_URL": "https://mastodon.test",
            "RSS_FEEDS": "http://feed1.com, http://feed2.com",
            # No RSS_FEED_URL
            "TOOT_VISIBILITY": "public",
        },
    )
    @patch("main.MastodonRSSBot")
    def test_main_loads_multiple_feeds_env(self, mock_bot_class):
        """Test that main() loads multiple feeds from environment variable"""
        # Ensure RSS_FEED_URL is not set from previous tests or env
        if "RSS_FEED_URL" in os.environ:
            del os.environ["RSS_FEED_URL"]

        from main import main

        mock_bot_instance = Mock()
        mock_bot_class.return_value = mock_bot_instance

        try:
            main()
        except Exception:
            pass

        mock_bot_class.assert_called_once()
        _, kwargs = mock_bot_class.call_args
        self.assertEqual(kwargs["feed_urls"], ["http://feed1.com", "http://feed2.com"])


if __name__ == "__main__":
    unittest.main()
