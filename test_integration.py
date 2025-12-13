"""Integration tests for Mastodon RSS Bot"""
import unittest
from unittest.mock import Mock, patch
import tempfile
import os
import time
from bot import MastodonRSSBot
import responses
import feedparser


class TestRSSFeedIntegration(unittest.TestCase):
    """Integration tests for RSS feed parsing"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'access_token': 'test_access_token',
            'instance_url': 'https://mastodon.test',
            'feed_url': 'https://example.com/feed.xml',
            'toot_visibility': 'public',
            'check_interval': 1,
            'state_file': tempfile.mktemp()
        }

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_config['state_file']):
            os.remove(self.test_config['state_file'])

    @responses.activate
    @patch('bot.Mastodon')
    def test_end_to_end_rss_to_mastodon(self, mock_mastodon):
        """Test complete flow from RSS feed to Mastodon post"""
        # Mock RSS feed response
        rss_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <link>https://example.com</link>
                <description>Test RSS Feed</description>
                <item>
                    <title>First Article</title>
                    <link>https://example.com/article1</link>
                    <description>This is the first article</description>
                </item>
                <item>
                    <title>Second Article</title>
                    <link>https://example.com/article2</link>
                    <description>This is the second article</description>
                </item>
            </channel>
        </rss>"""

        responses.add(
            responses.GET,
            'https://example.com/feed.xml',
            body=rss_feed,
            status=200,
            content_type='application/xml'
        )

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
        self.assertIn('First Article', calls[0][0][0])
        self.assertIn('https://example.com/article1', calls[0][0][0])
        self.assertIn('Second Article', calls[1][0][0])
        self.assertIn('https://example.com/article2', calls[1][0][0])

    @responses.activate
    @patch('bot.Mastodon')
    def test_atom_feed_parsing(self, mock_mastodon):
        """Test parsing Atom feeds"""
        atom_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test Atom Feed</title>
            <link href="https://example.com"/>
            <updated>2024-01-01T00:00:00Z</updated>
            <entry>
                <title>Atom Article</title>
                <link href="https://example.com/atom1"/>
                <id>https://example.com/atom1</id>
                <updated>2024-01-01T00:00:00Z</updated>
                <summary>This is an atom article</summary>
            </entry>
        </feed>"""

        responses.add(
            responses.GET,
            'https://example.com/feed.xml',
            body=atom_feed,
            status=200,
            content_type='application/atom+xml'
        )

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        self.assertEqual(count, 1)
        calls = mock_instance.status_post.call_args_list
        self.assertIn('Atom Article', calls[0][0][0])

    @responses.activate
    @patch('bot.Mastodon')
    def test_persistence_across_runs(self, mock_mastodon):
        """Test that processed entries persist across multiple bot runs"""
        rss_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Article 1</title>
                    <link>https://example.com/1</link>
                </item>
            </channel>
        </rss>"""

        responses.add(
            responses.GET,
            'https://example.com/feed.xml',
            body=rss_feed,
            status=200,
            content_type='application/xml'
        )

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

    @responses.activate
    @patch('bot.Mastodon')
    def test_incremental_feed_updates(self, mock_mastodon):
        """Test handling of new entries added to feed over time"""
        # Initial feed with 2 articles
        initial_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Article 1</title>
                    <link>https://example.com/1</link>
                </item>
                <item>
                    <title>Article 2</title>
                    <link>https://example.com/2</link>
                </item>
            </channel>
        </rss>"""

        responses.add(
            responses.GET,
            'https://example.com/feed.xml',
            body=initial_feed,
            status=200,
            content_type='application/xml'
        )

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        # First run
        bot = MastodonRSSBot(**self.test_config)
        count1 = bot.process_new_entries()
        self.assertEqual(count1, 2)

        # Update feed with 1 new article
        responses.reset()
        updated_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Article 3</title>
                    <link>https://example.com/3</link>
                </item>
                <item>
                    <title>Article 2</title>
                    <link>https://example.com/2</link>
                </item>
                <item>
                    <title>Article 1</title>
                    <link>https://example.com/1</link>
                </item>
            </channel>
        </rss>"""

        responses.add(
            responses.GET,
            'https://example.com/feed.xml',
            body=updated_feed,
            status=200,
            content_type='application/xml'
        )

        # Second run - should only post the new article
        count2 = bot.process_new_entries()
        self.assertEqual(count2, 1)

        # Verify only 3 total posts
        self.assertEqual(mock_instance.status_post.call_count, 3)

    @responses.activate
    @patch('bot.Mastodon')
    def test_network_error_handling(self, mock_mastodon):
        """Test handling of network errors when fetching feed"""
        responses.add(
            responses.GET,
            'https://example.com/feed.xml',
            body="Network error",
            status=500
        )

        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)
        count = bot.process_new_entries()

        # Should handle error gracefully
        self.assertEqual(count, 0)
        self.assertEqual(mock_instance.status_post.call_count, 0)

    @responses.activate
    @patch('bot.Mastodon')
    def test_malformed_xml_handling(self, mock_mastodon):
        """Test handling of malformed XML feeds"""
        malformed_feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Broken Feed
                <item>
                    <title>Article</title>
        """  # Intentionally malformed

        responses.add(
            responses.GET,
            'https://example.com/feed.xml',
            body=malformed_feed,
            status=200,
            content_type='application/xml'
        )

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
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'access_token': 'test_access_token',
            'instance_url': 'https://mastodon.test',
            'feed_url': 'https://example.com/feed.xml',
            'toot_visibility': 'public',
            'check_interval': 1,
            'state_file': tempfile.mktemp()
        }

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_config['state_file']):
            os.remove(self.test_config['state_file'])

    @patch('bot.Mastodon')
    def test_different_visibility_levels(self, mock_mastodon):
        """Test posting with different visibility levels"""
        mock_instance = Mock()
        mock_mastodon.return_value = mock_instance

        visibility_levels = ['public', 'unlisted', 'private', 'direct']

        for visibility in visibility_levels:
            self.test_config['toot_visibility'] = visibility
            bot = MastodonRSSBot(**self.test_config)
            bot.post_to_mastodon("Test status")

        # Verify all visibility levels were used
        calls = mock_instance.status_post.call_args_list
        for idx, visibility in enumerate(visibility_levels):
            self.assertEqual(calls[idx][1]['visibility'], visibility)

    @patch('bot.Mastodon')
    def test_retry_on_rate_limit(self, mock_mastodon):
        """Test that rate limit errors are handled appropriately"""
        from mastodon import MastodonRatelimitError

        mock_instance = Mock()
        # First call raises rate limit error, second succeeds
        mock_instance.status_post.side_effect = [
            MastodonRatelimitError("Rate limited"),
            None
        ]
        mock_mastodon.return_value = mock_instance

        bot = MastodonRSSBot(**self.test_config)

        # First attempt should fail
        result1 = bot.post_to_mastodon("Test status")
        self.assertFalse(result1)

        # Second attempt should succeed
        result2 = bot.post_to_mastodon("Test status")
        self.assertTrue(result2)


if __name__ == '__main__':
    unittest.main()
