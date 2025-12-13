"""Unit tests for Mastodon RSS Bot"""

import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import tempfile
import os
from bot import MastodonRSSBot
import feedparser


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
            "state_file": tempfile.mktemp(),
        }

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_config["state_file"]):
            os.remove(self.test_config["state_file"])

    @patch("bot.Mastodon")
    def test_bot_initialization(self, mock_mastodon):
        """Test bot initializes with correct configuration"""
        bot = MastodonRSSBot(**self.test_config)

        self.assertEqual(bot.feed_urls, self.test_config["feed_urls"])
        self.assertEqual(bot.toot_visibility, self.test_config["toot_visibility"])
        self.assertEqual(bot.check_interval, self.test_config["check_interval"])
        self.assertEqual(bot.state_file, self.test_config["state_file"])

        # Verify Mastodon client was initialized correctly
        mock_mastodon.assert_called_once_with(
            client_id=self.test_config["client_id"],
            client_secret=self.test_config["client_secret"],
            access_token=self.test_config["access_token"],
            api_base_url=self.test_config["instance_url"],
        )

    @patch("bot.Mastodon")
    def test_load_processed_entries_empty(self, mock_mastodon):
        """Test loading processed entries from non-existent file returns empty set"""
        bot = MastodonRSSBot(**self.test_config)
        entries = bot.load_processed_entries()

        self.assertEqual(entries, set())
        self.assertIsInstance(entries, set)

    @patch("bot.Mastodon")
    def test_load_processed_entries_existing(self, mock_mastodon):
        """Test loading processed entries from existing file"""
        # Create a temporary file with test data
        test_urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
        ]
        with open(self.test_config["state_file"], "w") as f:
            f.write("\n".join(test_urls))

        bot = MastodonRSSBot(**self.test_config)
        entries = bot.load_processed_entries()

        self.assertEqual(entries, set(test_urls))
        self.assertEqual(len(entries), 3)

    @patch("bot.Mastodon")
    def test_save_processed_entries(self, mock_mastodon):
        """Test saving processed entries to file"""
        bot = MastodonRSSBot(**self.test_config)
        test_entries = {
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
        }

        bot.save_processed_entries(test_entries)

        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(self.test_config["state_file"]))

        with open(self.test_config["state_file"], "r") as f:
            saved_entries = set(f.read().splitlines())

        self.assertEqual(saved_entries, test_entries)

    @patch("bot.Mastodon")
    def test_save_processed_entries_creates_directory(self, mock_mastodon):
        """Test that saving entries creates directory if it doesn't exist"""
        # Use a path with a non-existent directory
        test_dir = tempfile.mkdtemp()
        nested_path = os.path.join(test_dir, "subdir", "state.txt")
        self.test_config["state_file"] = nested_path

        bot = MastodonRSSBot(**self.test_config)
        bot.save_processed_entries({"https://example.com/1"})

        self.assertTrue(os.path.exists(nested_path))

        # Cleanup
        import shutil

        shutil.rmtree(test_dir)

    @patch("bot.Mastodon")
    def test_format_status(self, mock_mastodon):
        """Test status formatting from feed entry"""
        bot = MastodonRSSBot(**self.test_config)

        entry = {"title": "Test Article", "link": "https://example.com/article"}

        status = bot.format_status(entry)
        expected = "\nTest Article\n\nhttps://example.com/article"

        self.assertEqual(status, expected)

    @patch("bot.Mastodon")
    def test_format_status_missing_title(self, mock_mastodon):
        """Test status formatting with missing title"""
        bot = MastodonRSSBot(**self.test_config)

        entry = {"link": "https://example.com/article"}
        status = bot.format_status(entry)

        self.assertIn("Untitled", status)
        self.assertIn("https://example.com/article", status)

    @patch("bot.Mastodon")
    def test_post_to_mastodon_success(self, mock_mastodon):
        """Test successful posting to Mastodon"""
        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        result = bot.post_to_mastodon("Test status")

        self.assertTrue(result)
        mock_instance.status_post.assert_called_once_with(
            "Test status", visibility=self.test_config["toot_visibility"]
        )

    @patch("bot.Mastodon")
    def test_post_to_mastodon_failure(self, mock_mastodon):
        """Test handling of Mastodon posting failure"""
        mock_instance = Mock()
        mock_instance.status_post.side_effect = Exception("API Error")
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        result = bot.post_to_mastodon("Test status")

        self.assertFalse(result)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_parse_feed_success(self, mock_mastodon, mock_parse):
        """Test successful feed parsing"""
        mock_feed = Mock()
        mock_feed.entries = [{"title": "Test", "link": "https://example.com"}]
        mock_parse.return_value = mock_feed

        bot = MastodonRSSBot(**self.test_config)
        feed = bot.parse_feed("https://example.com/feed.xml")

        self.assertIsNotNone(feed)
        mock_parse.assert_called_once_with("https://example.com/feed.xml")

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_parse_feed_with_exception(self, mock_mastodon, mock_parse):
        """Test feed parsing with exception"""
        mock_parse.side_effect = Exception("Network error")

        bot = MastodonRSSBot(**self.test_config)
        feed = bot.parse_feed("https://example.com/feed.xml")

        self.assertIsNone(feed)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_new_entries_no_entries(self, mock_mastodon, mock_parse):
        """Test processing when feed has no entries"""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        self.assertEqual(count, 0)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_new_entries_all_new(self, mock_mastodon, mock_parse):
        """Test processing with all new entries"""
        # Mock feed with 3 entries
        mock_feed = Mock()
        mock_feed.entries = [
            {"title": "Article 1", "link": "https://example.com/1"},
            {"title": "Article 2", "link": "https://example.com/2"},
            {"title": "Article 3", "link": "https://example.com/3"},
        ]
        mock_parse.return_value = mock_feed

        # Mock Mastodon instance
        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        self.assertEqual(count, 3)
        self.assertEqual(mock_instance.status_post.call_count, 3)

        # Verify entries were saved
        saved_entries = bot.load_processed_entries()
        self.assertEqual(len(saved_entries), 3)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_new_entries_multiple_feeds(self, mock_mastodon, mock_parse):
        """Test processing with multiple feeds"""
        self.test_config["feed_urls"] = ["http://feed1.com", "http://feed2.com"]

        def side_effect(url):
            mock = Mock()
            if url == "http://feed1.com":
                mock.entries = [{"title": "1", "link": "http://link1.com"}]
            else:
                mock.entries = [{"title": "2", "link": "http://link2.com"}]
            return mock

        mock_parse.side_effect = side_effect

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        self.assertEqual(count, 2)
        self.assertEqual(mock_parse.call_count, 2)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_new_entries_some_processed(self, mock_mastodon, mock_parse):
        """Test processing with some entries already processed"""
        # Pre-populate processed entries
        processed = {"https://example.com/1", "https://example.com/2"}
        with open(self.test_config["state_file"], "w") as f:
            f.write("\n".join(processed))

        # Mock feed with 4 entries (2 old, 2 new)
        mock_feed = Mock()
        mock_feed.entries = [
            {
                "title": "Article 1",
                "link": "https://example.com/1",
            },  # Already processed
            {
                "title": "Article 2",
                "link": "https://example.com/2",
            },  # Already processed
            {"title": "Article 3", "link": "https://example.com/3"},  # New
            {"title": "Article 4", "link": "https://example.com/4"},  # New
        ]
        mock_parse.return_value = mock_feed

        # Mock Mastodon instance
        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        # Should only post 2 new entries
        self.assertEqual(count, 2)
        self.assertEqual(mock_instance.status_post.call_count, 2)

        # Verify all 4 entries are now in processed list
        saved_entries = bot.load_processed_entries()
        self.assertEqual(len(saved_entries), 4)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_new_entries_skip_no_url(self, mock_mastodon, mock_parse):
        """Test that entries without URLs are skipped"""
        mock_feed = Mock()
        mock_feed.entries = [
            {"title": "Article without URL"},  # No link field
            {"title": "Article with URL", "link": "https://example.com/1"},
        ]
        mock_parse.return_value = mock_feed

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        # Should only process 1 entry (the one with URL)
        self.assertEqual(count, 1)
        self.assertEqual(mock_instance.status_post.call_count, 1)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_process_new_entries_posting_failure(self, mock_mastodon, mock_parse):
        """Test that failed posts don't get marked as processed"""
        mock_feed = Mock()
        mock_feed.entries = [
            {"title": "Article 1", "link": "https://example.com/1"},
        ]
        mock_parse.return_value = mock_feed

        # Mock Mastodon to fail
        mock_instance = Mock()
        mock_instance.status_post.side_effect = Exception("API Error")
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        # No entries should be counted as posted
        self.assertEqual(count, 0)

        # Entry should not be marked as processed
        saved_entries = bot.load_processed_entries()
        self.assertEqual(len(saved_entries), 0)


class TestMainEntry(unittest.TestCase):
    """Test cases for main.py entry point"""

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
            state_file="/tmp/test_state.txt",
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
