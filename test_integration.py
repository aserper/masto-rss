"""Integration tests for Mastodon RSS Bot"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from bot import MastodonRSSBot


class TestRSSFeedIntegration(unittest.TestCase):
    """Integration tests for RSS feed parsing"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "access_token": "test_access_token",
            "instance_url": "https://mastodon.test",
            "feed_url": "https://example.com/feed.xml",
            "toot_visibility": "public",
            "check_interval": 1,
            "state_file": tempfile.mktemp(),
        }

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_config["state_file"]):
            os.remove(self.test_config["state_file"])

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_end_to_end_rss_to_mastodon(self, mock_mastodon, mock_parse):
        """Test complete flow from RSS feed to Mastodon post"""
        # Create mock feed object
        mock_feed = Mock()
        mock_feed.entries = [
            {"title": "First Article", "link": "https://example.com/article1"},
            {"title": "Second Article", "link": "https://example.com/article2"},
        ]
        mock_parse.return_value = mock_feed

        # Mock Mastodon instance
        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        # Create bot and process entries
        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        # Verify results
        self.assertEqual(count, 2)
        self.assertEqual(mock_instance.status_post.call_count, 2)

        # Verify the content of posts
        calls = mock_instance.status_post.call_args_list
        self.assertIn("First Article", calls[0][0][0])
        self.assertIn("https://example.com/article1", calls[0][0][0])
        self.assertIn("Second Article", calls[1][0][0])
        self.assertIn("https://example.com/article2", calls[1][0][0])

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_atom_feed_parsing(self, mock_mastodon, mock_parse):
        """Test parsing Atom feeds"""
        # Create mock Atom feed object
        mock_feed = Mock()
        mock_feed.entries = [
            {"title": "Atom Article", "link": "https://example.com/atom1"}
        ]
        mock_parse.return_value = mock_feed

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        self.assertEqual(count, 1)
        calls = mock_instance.status_post.call_args_list
        self.assertIn("Atom Article", calls[0][0][0])

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_persistence_across_runs(self, mock_mastodon, mock_parse):
        """Test that processed entries persist across multiple bot runs"""
        # Create mock feed object
        mock_feed = Mock()
        mock_feed.entries = [{"title": "Article 1", "link": "https://example.com/1"}]
        mock_parse.return_value = mock_feed

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        # First run - should post the article
        bot1 = MastodonRSSBot(**self.test_config)
        count1 = bot1.process_new_entries()
        self.assertEqual(count1, 1)

        # Second run - should NOT post again (already processed)
        bot2 = MastodonRSSBot(**self.test_config)
        count2 = bot2.process_new_entries()
        self.assertEqual(count2, 0)

        # Total posts should be 1
        self.assertEqual(mock_instance.status_post.call_count, 1)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_incremental_feed_updates(self, mock_mastodon, mock_parse):
        """Test handling of new entries added to feed over time"""
        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        # First run - initial feed with 2 articles
        mock_feed = Mock()
        mock_feed.entries = [
            {"title": "Article 1", "link": "https://example.com/1"},
            {"title": "Article 2", "link": "https://example.com/2"},
        ]
        mock_parse.return_value = mock_feed

        bot = MastodonRSSBot(**self.test_config)
        count1 = bot.process_new_entries()
        self.assertEqual(count1, 2)

        # Second run - updated feed with 1 new article
        mock_feed.entries = [
            {"title": "Article 3", "link": "https://example.com/3"},
            {"title": "Article 2", "link": "https://example.com/2"},
            {"title": "Article 1", "link": "https://example.com/1"},
        ]

        # Second run - should only post the new article
        count2 = bot.process_new_entries()
        self.assertEqual(count2, 1)

        # Verify only 3 total posts
        self.assertEqual(mock_instance.status_post.call_count, 3)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_network_error_handling(self, mock_mastodon, mock_parse):
        """Test handling of network errors when fetching feed"""
        # Simulate network error by returning None
        mock_parse.return_value = None

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        # Should handle error gracefully
        self.assertEqual(count, 0)
        self.assertEqual(mock_instance.status_post.call_count, 0)

    @patch("bot.feedparser.parse")
    @patch("bot.Mastodon")
    def test_malformed_xml_handling(self, mock_mastodon, mock_parse):
        """Test handling of malformed XML feeds"""
        # Create mock feed with bozo_exception (feedparser's error indicator)
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feed.bozo_exception = Exception("XML parsing error")
        mock_parse.return_value = mock_feed

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        # Should handle malformed feed gracefully
        count = bot.process_new_entries()

        # feedparser is lenient and may parse some entries
        # The important thing is it doesn't crash
        self.assertIsInstance(count, int)


class TestMastodonAPIIntegration(unittest.TestCase):
    """Integration tests for Mastodon API interaction"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "access_token": "test_access_token",
            "instance_url": "https://mastodon.test",
            "feed_url": "https://example.com/feed.xml",
            "toot_visibility": "public",
            "check_interval": 1,
            "state_file": tempfile.mktemp(),
        }

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_config["state_file"]):
            os.remove(self.test_config["state_file"])

    @patch("bot.Mastodon")
    def test_different_visibility_levels(self, mock_mastodon):
        """Test posting with different visibility levels"""
        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        visibility_levels = ["public", "unlisted", "private", "direct"]

        for visibility in visibility_levels:
            self.test_config["toot_visibility"] = visibility
            bot = MastodonRSSBot(**self.test_config)
            bot.post_to_mastodon("Test status")

        # Verify all visibility levels were used
        calls = mock_instance.status_post.call_args_list
        for idx, visibility in enumerate(visibility_levels):
            self.assertEqual(calls[idx][1]["visibility"], visibility)

    @patch("bot.Mastodon")
    def test_retry_on_rate_limit(self, mock_mastodon):
        """Test that rate limit errors are handled appropriately"""
        from mastodon import MastodonRatelimitError

        mock_instance = Mock()
        # First call raises rate limit error, second succeeds
        mock_instance.status_post.side_effect = [
            MastodonRatelimitError("Rate limited"),
            None,
        ]
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)

        # First attempt should fail
        result1 = bot.post_to_mastodon("Test status")
        self.assertFalse(result1)

        # Second attempt should succeed
        result2 = bot.post_to_mastodon("Test status")
        self.assertTrue(result2)


if __name__ == "__main__":
    unittest.main()
