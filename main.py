import feedparser
from mastodon import Mastodon
import os
import time

# --- Configuratie ---
# Haal configuratie op uit omgevingsvariabelen
MASTODON_CLIENT_ID = os.environ.get('MASTODON_CLIENT_ID')
MASTODON_CLIENT_SECRET = os.environ.get('MASTODON_CLIENT_SECRET')
MASTODON_ACCESS_TOKEN = os.environ.get('MASTODON_ACCESS_TOKEN')
MASTODON_INSTANCE_URL = os.environ.get('MASTODON_INSTANCE_URL')
RSS_FEED_URL = os.environ.get('RSS_FEED_URL')

# Optionele configuratie met standaardwaarden
TOOT_VISIBILITY = os.environ.get('TOOT_VISIBILITY', 'public') # Standaard op 'public'
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', 3600)) # Standaard op 1 uur (3600s)

# Hashtags om toe te voegen aan elke post, gescheiden door spaties
HASHTAGS = os.environ.get('MASTO_RSS_HASHTAGS', '') 

# Bestand om de verwerkte entry-URL's op te slaan.
# De /state map is bedoeld voor een Docker-setup voor persistente data.
PROCESSED_ENTRIES_FILE = '/state/processed_entries.txt'

# Controleer of alle benodigde configuratie aanwezig is
if not all([MASTODON_CLIENT_ID, MASTODON_CLIENT_SECRET, MASTODON_ACCESS_TOKEN, MASTODON_INSTANCE_URL, RSS_FEED_URL]):
    print("Fout: Niet alle vereiste omgevingsvariabelen zijn ingesteld.")
    print("Zorg ervoor dat MASTODON_CLIENT_ID, MASTODON_CLIENT_SECRET, MASTODON_ACCESS_TOKEN, MASTODON_INSTANCE_URL, en RSS_FEED_URL zijn ingesteld.")
    exit(1)

# --- Mastodon Initialisatie ---
try:
    mastodon = Mastodon(
        client_id=MASTODON_CLIENT_ID,
        client_secret=MASTODON_CLIENT_SECRET,
        access_token=MASTODON_ACCESS_TOKEN,
        api_base_url=MASTODON_INSTANCE_URL
    )
    # Verifieer de inloggegevens
    mastodon.account_verify_credentials()
    print("Succesvol ingelogd bij Mastodon.")
except Exception as e:
    print(f"Fout bij het initialiseren van de Mastodon client: {e}")
    exit(1)

# --- Functies ---

def load_processed_entries():
    """Laadt verwerkte entry-URL's uit een bestand."""
    # Zorg ervoor dat de /state map bestaat
    os.makedirs(os.path.dirname(PROCESSED_ENTRIES_FILE), exist_ok=True)
    try:
        with open(PROCESSED_ENTRIES_FILE, 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

def save_processed_entries(processed_entries):
    """Slaat verwerkte entry-URL's op in een bestand."""
    with open(PROCESSED_ENTRIES_FILE, 'w') as file:
        file.write('\n'.join(processed_entries))

def format_hashtags(hashtag_string):
    """Formatteert een string van hashtags naar een correcte lijst."""
    if not hashtag_string:
        return ""
    # Split de string op spaties, verwijder eventuele lege items
    tags = filter(None, hashtag_string.split(' '))
    # Voeg een '#' toe aan elke tag (als deze er nog niet is) en voeg ze samen
    return " ".join([f"#{tag.lstrip('#')}" for tag in tags])

def check_and_post_new_items():
    """Controleert de RSS-feed en post alleen het laatste item als het nieuw is."""
    
    # Formatteer de hashtags eenmalig en geef feedback aan de gebruiker
    formatted_hashtags = format_hashtags(HASHTAGS)
    if formatted_hashtags:
        print(f"Hashtags geconfigureerd voor deze sessie: {formatted_hashtags}")
    else:
        print("INFO: Geen hashtags geconfigureerd (omgevingsvariabele MASTO_RSS_HASHTAGS is leeg of niet ingesteld).")


    while True:
        print(f"Controleren op nieuwe RSS-items van: {RSS_FEED_URL}")
        
        # Laad verwerkte entry-URL's uit het bestand
        processed_entries = load_processed_entries()

        # Parse de RSS-feed
        feed = feedparser.parse(RSS_FEED_URL)
        
        if feed.bozo:
            print(f"Waarschuwing: De RSS-feed is mogelijk niet goed geformatteerd. Fout: {feed.bozo_exception}")

        # Controleer of er überhaupt items in de feed zijn
        if not feed.entries:
            print("Geen items gevonden in de RSS-feed.")
        else:
            # Neem alleen het laatste item (de eerste in de lijst, dit is de meest recente)
            latest_entry = feed.entries[0]
            entry_url = latest_entry.get('link')
            entry_title = latest_entry.get('title', 'Geen titel')

            if not entry_url:
                print(f"Laatste item '{entry_title}' overgeslagen omdat het geen link heeft.")
            # Controleer of het laatste item nog niet is gepost
            elif entry_url not in processed_entries:
                print(f"Nieuw laatste item gevonden: {entry_title}")
                
                # Stel de Mastodon-status samen
                status_parts = [entry_title, entry_url]
                if formatted_hashtags:
                    status_parts.append(formatted_hashtags)
                
                status = "\n\n".join(status_parts)

                # Post de status naar Mastodon
                try:
                    print(f"Bezig met posten: {status}")
                    mastodon.status_post(status, visibility=TOOT_VISIBILITY)
                    print("Post succesvol geplaatst.")
                    
                    # Voeg de URL toe aan de set van verwerkte items en sla direct op
                    processed_entries.add(entry_url)
                    save_processed_entries(processed_entries)
                except Exception as e:
                    print(f"Fout bij het posten naar Mastodon: {e}")
            else:
                # Als de link al in de set zit, is het bericht al gepost.
                print("Het laatste item is al gepost.")

        print(f"Wachten voor {CHECK_INTERVAL} seconden...")
        time.sleep(CHECK_INTERVAL)

# --- Hoofdprogramma ---
if __name__ == "__main__":
    check_and_post_new_items()
