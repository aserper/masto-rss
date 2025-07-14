import feedparser
from mastodon import Mastodon
import os
import time
from collections import deque

# --- Configuratie ---
# Haal configuratie op uit omgevingsvariabelen
MASTODON_CLIENT_ID = os.environ.get('MASTODON_CLIENT_ID')
MASTODON_CLIENT_SECRET = os.environ.get('MASTODON_CLIENT_SECRET')
MASTODON_ACCESS_TOKEN = os.environ.get('MASTODON_ACCESS_TOKEN')
MASTODON_INSTANCE_URL = os.environ.get('MASTODON_INSTANCE_URL')
RSS_FEED_URL = os.environ.get('RSS_FEED_URL')

# Optionele configuratie met standaardwaarden
TOOT_VISIBILITY = os.environ.get('TOOT_VISIBILITY', 'public')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 3600))
HASHTAGS = os.environ.get('MASTO_RSS_HASHTAGS', '') 
MAX_HISTORY_SIZE = int(os.environ.get('MAX_HISTORY_SIZE', 500))

# Bestand om de verwerkte entry-URL's op te slaan.
PROCESSED_ENTRIES_FILE = '/state/processed_entries.txt'

# Controleer of alle benodigde configuratie aanwezig is
if not all([MASTODON_CLIENT_ID, MASTODON_CLIENT_SECRET, MASTODON_ACCESS_TOKEN, MASTODON_INSTANCE_URL, RSS_FEED_URL]):
    print("Fout: Niet alle vereiste omgevingsvariabelen zijn ingesteld.")
    exit(1)

# --- Mastodon Initialisatie ---
try:
    mastodon = Mastodon(
        client_id=MASTODON_CLIENT_ID,
        client_secret=MASTODON_CLIENT_SECRET,
        access_token=MASTODON_ACCESS_TOKEN,
        api_base_url=MASTODON_INSTANCE_URL
    )
    mastodon.account_verify_credentials()
    print("Succesvol ingelogd bij Mastodon.")
except Exception as e:
    print(f"Fout bij het initialiseren van de Mastodon client: {e}")
    exit(1)

# --- Functies ---

def load_processed_entries():
    """Laadt verwerkte entry-URL's uit een bestand in een deque."""
    os.makedirs(os.path.dirname(PROCESSED_ENTRIES_FILE), exist_ok=True)
    try:
        with open(PROCESSED_ENTRIES_FILE, 'r') as file:
            lines = file.read().splitlines()
            return deque(lines, maxlen=MAX_HISTORY_SIZE)
    except FileNotFoundError:
        return deque(maxlen=MAX_HISTORY_SIZE)

def save_processed_entries(processed_entries_deque):
    """Slaat de verwerkte entry-URL's van de deque op in een bestand."""
    with open(PROCESSED_ENTRIES_FILE, 'w') as file:
        file.write('\n'.join(processed_entries_deque))

def format_hashtags(hashtag_string):
    """
    Formatteert een string van hashtags naar een correcte lijst.
    Deze functie is robuust en verwijdert eventuele aanhalingstekens.
    """
    if not hashtag_string:
        return ""
    
    # BELANGRIJKE FIX: Verwijder eventuele aanhalingstekens en witruimte
    # van de begin- en eindkant van de string.
    clean_string = hashtag_string.strip(' "\'')

    # Split de schone string op spaties en filter lege items eruit
    tags = filter(None, clean_string.split(' '))
    
    # Voeg een '#' toe aan elke tag (indien nodig) en voeg ze samen
    return " ".join([f"#{tag.lstrip('#')}" for tag in tags])

def check_and_post_new_items():
    """Controleert de RSS-feed en post alleen het laatste item als het nieuw is."""
    
    formatted_hashtags = format_hashtags(HASHTAGS)
    if formatted_hashtags:
        print(f"Hashtags geconfigureerd: {formatted_hashtags}")
    else:
        print("INFO: Geen hashtags geconfigureerd.")
    
    print(f"INFO: De geschiedenis wordt beperkt tot de laatste {MAX_HISTORY_SIZE} items.")

    processed_entries = load_processed_entries()

    while True:
        print(f"Controleren op nieuwe RSS-items van: {RSS_FEED_URL}")
        
        feed = feedparser.parse(RSS_FEED_URL)
        
        if feed.bozo:
            print(f"Waarschuwing: RSS-feed mogelijk niet goed geformatteerd. Fout: {feed.bozo_exception}")

        if not feed.entries:
            print("Geen items gevonden in de RSS-feed.")
        else:
            latest_entry = feed.entries[0]
            entry_url = latest_entry.get('link')
            entry_title = latest_entry.get('title', 'Geen titel')

            if not entry_url:
                print(f"Laatste item '{entry_title}' overgeslagen (geen link).")
            elif entry_url not in processed_entries:
                print(f"Nieuw laatste item gevonden: {entry_title}")
                
                status_parts = [entry_title, entry_url]
                if formatted_hashtags:
                    status_parts.append(formatted_hashtags)
                
                status = "\n\n".join(status_parts)

                try:
                    print(f"Bezig met posten: {status}")
                    mastodon.status_post(status, visibility=TOOT_VISIBILITY)
                    print("Post succesvol geplaatst.")
                    
                    processed_entries.append(entry_url)
                    save_processed_entries(processed_entries)

                except Exception as e:
                    print(f"Fout bij het posten naar Mastodon: {e}")
            else:
                print("Het laatste item is al gepost.")

        print(f"Wachten voor {CHECK_INTERVAL} seconden...")
        time.sleep(int(CHECK_INTERVAL))

# --- Hoofdprogramma ---
if __name__ == "__main__":
    check_and_post_new_items()
