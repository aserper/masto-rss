import feedparser
from mastodon import Mastodon
import os
import time
from collections import deque

# --- Configuration ---
# Get configuration from environment variables
MASTODON_CLIENT_ID = os.environ.get('MASTODON_CLIENT_ID')
MASTODON_CLIENT_SECRET = os.environ.get('MASTODON_CLIENT_SECRET')
MASTODON_ACCESS_TOKEN = os.environ.get('MASTODON_ACCESS_TOKEN')
MASTODON_INSTANCE_URL = os.environ.get('MASTODON_INSTANCE_URL')
RSS_FEED_URL = os.environ.get('RSS_FEED_URL')

# Optional configuration with default values
TOOT_VISIBILITY = os.environ.get('TOOT_VISIBILITY', 'public')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 3600))
HASHTAGS = os.environ.get('MASTO_RSS_HASHTAGS', '') 
MAX_HISTORY_SIZE = int(os.environ.get('MAX_HISTORY_SIZE', 500))

# NEW: Template for the toot format.
# Use {title}, {link}, and {hashtags} as placeholders.
DEFAULT_TEMPLATE = '{title}\n\n{link}\n\n{hashtags}'
TOOT_TEMPLATE = os.environ.get('TOOT_TEMPLATE', DEFAULT_TEMPLATE)

# File to store the processed entry URLs.
PROCESSED_ENTRIES_FILE = '/state/processed_entries.txt'

# Check if all required configuration is present
if not all([MASTODON_CLIENT_ID, MASTODON_CLIENT_SECRET, MASTODON_ACCESS_TOKEN, MASTODON_INSTANCE_URL, RSS_FEED_URL]):
    print("Error: Not all required environment variables are set.")
    exit(1)

# --- Mastodon Initialization ---
try:
    mastodon = Mastodon(
        client_id=MASTODON_CLIENT_ID,
        client_secret=MASTODON_CLIENT_SECRET,
        access_token=MASTODON_ACCESS_TOKEN,
        api_base_url=MASTODON_INSTANCE_URL
    )
    mastodon.account_verify_credentials()
    print("Successfully logged in to Mastodon.")
except Exception as e:
    print(f"Error initializing Mastodon client: {e}")
    exit(1)

# --- Functions ---

def load_processed_entries():
    """Loads processed entry URLs from a file into a deque."""
    os.makedirs(os.path.dirname(PROCESSED_ENTRIES_FILE), exist_ok=True)
    try:
        with open(PROCESSED_ENTRIES_FILE, 'r') as file:
            lines = file.read().splitlines()
            return deque(lines, maxlen=MAX_HISTORY_SIZE)
    except FileNotFoundError:
        return deque(maxlen=MAX_HISTORY_SIZE)

def save_processed_entries(processed_entries_deque):
    """Saves the processed entry URLs from the deque to a file."""
    with open(PROCESSED_ENTRIES_FILE, 'w') as file:
        file.write('\n'.join(processed_entries_deque))

def format_hashtags(hashtag_string):
    """Formats a string of hashtags into a correct list."""
    if not hashtag_string:
        return ""
    clean_string = hashtag_string.strip(' "\'')
    tags = filter(None, clean_string.split(' '))
    return " ".join([f"#{tag.lstrip('#')}" for tag in tags])

def check_and_post_new_items():
    """Checks the RSS feed and only posts the latest item if it's new."""
    
    formatted_hashtags = format_hashtags(HASHTAGS)
    if formatted_hashtags:
        print(f"Hashtags configured: {formatted_hashtags}")
    else:
        print("INFO: No hashtags configured.")
    
    print(f"INFO: Using toot template: {TOOT_TEMPLATE.replace(chr(10), ' ')}")
    
    processed_entries = load_processed_entries()

    while True:
        print(f"Checking for new RSS items from: {RSS_FEED_URL}")
        
        feed = feedparser.parse(RSS_FEED_URL)
        
        if feed.bozo:
            print(f"Warning: RSS feed may be malformed. Error: {feed.bozo_exception}")

        if not feed.entries:
            print("No items found in the RSS feed.")
        else:
            latest_entry = feed.entries[0]
            entry_url = latest_entry.get('link')
            entry_title = latest_entry.get('title', 'No title')

            if not entry_url:
                print(f"Skipping latest item '{entry_title}' (no link).")
            elif entry_url not in processed_entries:
                print(f"Found new latest item: {entry_title}")
                
                # Compose the Mastodon status based on the template
                status = TOOT_TEMPLATE.format(
                    title=entry_title, 
                    link=entry_url, 
                    hashtags=formatted_hashtags
                ).strip()

                try:
                    print(f"Posting: {status.replace(chr(10), ' ')}")
                    mastodon.status_post(status, visibility=TOOT_VISIBILITY)
                    print("Post successful.")
                    
                    processed_entries.append(entry_url)
                    save_processed_entries(processed_entries)

                except Exception as e:
                    print(f"Error posting to Mastodon: {e}")
            else:
                print("The latest item has already been posted.")

        print(f"Waiting for {CHECK_INTERVAL} seconds...")
        time.sleep(int(CHECK_INTERVAL))

# --- Main Program ---
if __name__ == "__main__":
    check_and_post_new_items()
