import feedparser
from mastodon import Mastodon
import os
import time
# Replace these with your Mastodon application details and access token
MASTODON_CLIENT_ID = os.environ['MASTODON_CLIENT_ID']
MASTODON_CLIENT_SECRET = os.environ['MASTODON_CLIENT_SECRET']
MASTODON_ACCESS_TOKEN = os.environ['MASTODON_ACCESS_TOKEN']
MASTODON_INSTANCE_URL = os.environ['MASTODON_INSTANCE_URL']

# RSS feed URL
RSS_FEED_URL = os.environ['RSS_FEED_URL']

# File to store the processed entry URLs
PROCESSED_ENTRIES_FILE = 'processed_entries.txt'

# Time delay between RSS checks (in seconds)
CHECK_INTERVAL = os.environ['CHECK_INTERVAL']  # Check interval in seconds

# Initialize Mastodon client
mastodon = Mastodon(
    client_id=MASTODON_CLIENT_ID,
    client_secret=MASTODON_CLIENT_SECRET,
    access_token=MASTODON_ACCESS_TOKEN,
    api_base_url=MASTODON_INSTANCE_URL
)

# Function to load processed entry URLs from a file
def load_processed_entries():
    try:
        with open(PROCESSED_ENTRIES_FILE, 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Function to save processed entry URLs to a file
def save_processed_entries(processed_entries):
    with open(PROCESSED_ENTRIES_FILE, 'w') as file:
        file.write('\n'.join(processed_entries))

# Function to check and post new RSS items
def check_and_post_new_items():
    while True:
        print("Checking for new RSS items...")
        # Load processed entry URLs from the file
        processed_entries = load_processed_entries()

        # Parse the RSS feed
        feed = feedparser.parse(RSS_FEED_URL)

        for entry in feed.entries:
            entry_url = entry.link

            # Check if the entry is new (not in the processed_entries set)
            if entry_url not in processed_entries:
                print(f"Found a new RSS item: {entry.title}")
                # Create a Mastodon status
                status = f"\n{entry.title}\n\n{entry.link}"

                # Post the status to Mastodon
                mastodon.status_post(status)

                # Add the entry URL to the processed_entries set
                processed_entries.add(entry_url)

        # Save the updated processed_entries set to the file
        save_processed_entries(processed_entries)

        print("Sleeping for", CHECK_INTERVAL, "seconds...")
        # Wait for the specified interval before checking again
        time.sleep(int(CHECK_INTERVAL))

if __name__ == "__main__":
    check_and_post_new_items()