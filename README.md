![Masto-RSS Header](header.jpg)

# Masto-RSS

[![CI/CD](https://img.shields.io/github/actions/workflow/status/aserper/masto-rss/ci.yml?style=for-the-badge&logo=github&label=CI/CD)](https://github.com/aserper/masto-rss/actions/workflows/ci.yml)
[![Docker Hub](https://img.shields.io/badge/docker%20hub-amitserper%2Fmasto--rss-blue?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/amitserper/masto-rss)
[![GHCR](https://img.shields.io/badge/ghcr.io-masto--rss-blue?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/aserper/masto-rss/pkgs/container/masto-rss)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-yellow.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/aserper/masto-rss.svg?style=social)](https://github.com/aserper/masto-rss)
[![GitHub forks](https://img.shields.io/github/forks/aserper/masto-rss.svg?style=social&label=Fork)](https://github.com/aserper/masto-rss/network)

A simple, lightweight Mastodon bot that automatically posts updates from RSS feeds to the Fediverse. Built with Python and designed to run seamlessly in Docker with multiarch support (amd64 & arm64).

## Features

- Automatically monitors RSS/Atom feeds and posts new items to Mastodon
- Persistent state tracking to avoid duplicate posts
- Configurable post visibility (public, unlisted, private, direct)
- Lightweight Python Slim-based Docker image
- Multiarch support (amd64 & arm64) for broad compatibility
- Continuous monitoring with configurable check intervals

## Quick Start

### Using Docker (Recommended)

The easiest way to run Masto-RSS is using the pre-built multiarch Docker images available on both Docker Hub and GitHub Container Registry.

#### Pull from Docker Hub

```bash
docker pull amitserper/masto-rss:latest
```

#### Pull from GitHub Container Registry

```bash
docker pull ghcr.io/aserper/masto-rss:latest
```

#### Run the Bot

```bash
docker run -d \
  --name masto-rss-bot \
  -e MASTODON_CLIENT_ID="your_client_id" \
  -e MASTODON_CLIENT_SECRET="your_client_secret" \
  -e MASTODON_ACCESS_TOKEN="your_access_token" \
  -e MASTODON_INSTANCE_URL="https://mastodon.social" \
  -e RSS_FEED_URL="https://example.com/feed.xml" \
  -e TOOT_VISIBILITY="public" \
  -e CHECK_INTERVAL="300" \
  -v /path/to/state:/state \
  amitserper/masto-rss:latest
```

> **Important:** Use a bind mount for `/state` to persist the list of processed feed items across container restarts.

### Using Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  masto-rss:
    image: amitserper/masto-rss:latest
    # Or use GHCR: ghcr.io/aserper/masto-rss:latest
    container_name: masto-rss-bot
    restart: unless-stopped
    environment:
      MASTODON_CLIENT_ID: "your_client_id"
      MASTODON_CLIENT_SECRET: "your_client_secret"
      MASTODON_ACCESS_TOKEN: "your_access_token"
      MASTODON_INSTANCE_URL: "https://mastodon.social"
      RSS_FEED_URL: "https://example.com/feed.xml"
      TOOT_VISIBILITY: "public"
      CHECK_INTERVAL: "300"
    volumes:
      - ./state:/state
```

Then run:

```bash
docker-compose up -d
```


### Multiple Feeds
To monitor multiple feeds, you can either:
- Use the `RSS_FEEDS` environment variable (comma-separated list)
- Use the `FEEDS_FILE` environment variable (path to file with one URL per line)

#### Run with Multiple Feeds (Docker)

```bash
docker run -d \
  --name masto-rss-bot \
  -e MASTODON_CLIENT_ID="your_client_id" \
  -e MASTODON_CLIENT_SECRET="your_client_secret" \
  -e MASTODON_ACCESS_TOKEN="your_access_token" \
  -e MASTODON_INSTANCE_URL="https://mastodon.social" \
  -e RSS_FEEDS="https://feed1.com/rss,https://feed2.com/rss" \
  -e TOOT_VISIBILITY="public" \
  -e CHECK_INTERVAL="300" \
  -v /path/to/state:/state \
  amitserper/masto-rss:latest
```

## Configuration

All configuration is done via environment variables:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `MASTODON_CLIENT_ID` | Mastodon application client ID | Yes | `abc123...` |
| `MASTODON_CLIENT_SECRET` | Mastodon application client secret | Yes | `xyz789...` |
| `MASTODON_ACCESS_TOKEN` | Mastodon access token | Yes | `token123...` |
| `MASTODON_INSTANCE_URL` | URL of your Mastodon instance | Yes | `https://mastodon.social` |
| `RSS_FEED_URL` | Single RSS/Atom feed URL (Legacy) | No* | `https://example.com/feed.xml` |
| `RSS_FEEDS` | Comma-separated list of feed URLs | No* | `https://site1.com,https://site2.com` |
| `FEEDS_FILE` | Path to file containing list of feed URLs | No* | `/config/feeds.txt` |
| `TOOT_VISIBILITY` | Post visibility level | Yes | `public`, `unlisted`, `private`, or `direct` |
| `CHECK_INTERVAL` | Seconds between feed checks | Yes | `300` (5 minutes) |
| `PROCESSED_ENTRIES_FILE`| Custom path for state file | No | `/state/processed.txt` |

\* At least one of `RSS_FEED_URL`, `RSS_FEEDS`, or `FEEDS_FILE` must be provided.

### Getting Mastodon API Credentials

1. Log into your Mastodon instance
2. Go to **Settings** → **Development** → **New Application**
3. Give it a name (e.g., "RSS Bot")
4. Set scopes to `write:statuses`
5. Save and copy the client ID, client secret, and access token

## Building from Source

### Build Locally

```bash
git clone https://github.com/aserper/masto-rss.git
cd masto-rss
docker build -t masto-rss .
```

### Build Multiarch Images

```bash
# Set up buildx
docker buildx create --use

# Build for both architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/masto-rss:latest \
  --push \
  .
```

## Running Without Docker

If you prefer to run the bot directly with Python:

```bash
# Clone the repository
git clone https://github.com/aserper/masto-rss.git
cd masto-rss

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MASTODON_CLIENT_ID="your_client_id"
export MASTODON_CLIENT_SECRET="your_client_secret"
export MASTODON_ACCESS_TOKEN="your_access_token"
export MASTODON_INSTANCE_URL="https://mastodon.social"
export RSS_FEED_URL="https://example.com/feed.xml"
export TOOT_VISIBILITY="public"
export CHECK_INTERVAL="300"

# Run the bot
python main.py
```

> **Note:** When running without Docker, the bot stores its state in `/state/processed_entries.txt`. Make sure this directory exists or modify [main.py](main.py#L15) to use a different path.

## How It Works

1. The bot fetches the RSS feed at regular intervals (defined by `CHECK_INTERVAL`)
2. For each feed item, it checks if the item's URL has been processed before
3. If the item is new, it posts to Mastodon with the format: `{title}\n\n{link}`
4. The item URL is saved to prevent duplicate posts
5. The process repeats indefinitely

## Architecture

- **Base Image:** Python 3.12-slim (stable & compatible)
- **Python Version:** 3.10+
- **Platforms:** linux/amd64, linux/arm64
- **Dependencies:** feedparser, mastodon.py (see [requirements.txt](requirements.txt))

## State Persistence

The bot maintains state in `/state/processed_entries.txt` to track which feed items have already been posted. This prevents duplicate posts across restarts.

**Important:** Always mount `/state` as a volume to preserve this state file.

## Contributing

Contributions are welcome! Feel free to:

- Report bugs by opening an issue
- Submit pull requests for improvements
- Suggest new features or enhancements

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Support

If you find this project useful, please consider giving it a star on GitHub!

## Links

- [Docker Hub Repository](https://hub.docker.com/r/amitserper/masto-rss)
- [GitHub Container Registry](https://github.com/aserper/masto-rss/pkgs/container/masto-rss)
- [Source Code](https://github.com/aserper/masto-rss)
- [Issues](https://github.com/aserper/masto-rss/issues)
