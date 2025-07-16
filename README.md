# Masto-RSS Advanced Bot

A flexible and robust Python script to automatically post the latest entry from an RSS feed to Mastodon, designed to run continuously in a Docker container.

This project is based on the original concept of [masto-rss](https://github.com/piko-system/masto-rss) but has been significantly rewritten and extended with modern features for stability and customization.

## Features

* **Posts Only the Latest Item**: Checks an RSS feed periodically and posts only the single most recent entry, preventing feed spam.
* **Prevents Duplicates**: Keeps a history of posted items to ensure the same link is never posted twice.
* **History Limit**: The history file is automatically pruned to a configurable size (`MAX_HISTORY_SIZE`) to prevent it from growing indefinitely.
* **Custom Toot Format**: Fully customize the look of your posts using a template string with placeholders (`{title}`, `{link}`, `{hashtags}`).
* **Hashtag Support**: Automatically append a configurable list of hashtags to every post.
* **Dockerized**: Runs as a pre-built container image for easy, reliable, and isolated deployment. You don't need to manage Python or dependencies.
* **Robust Error Handling**: Designed to run forever, it handles connection errors to the RSS feed or Mastodon gracefully without crashing.

## Getting Started

The recommended and simplest way to run this bot is by using the pre-built Docker image from Docker Hub with Docker Compose.

### 1. Prerequisites

* Docker and Docker Compose installed on your system.
* A Mastodon account and an application set up via **Preferences > Development**. You will need the **Client Key**, **Client Secret**, and **Access Token**.

### 2. Configuration

You only need to create one file: `docker-compose.yml`.

First, create a directory for your project and navigate into it:

```bash
mkdir my-masto-bot
cd my-masto-bot
```

Next, create a file named `docker-compose.yml` and paste the following content into it. **You must edit the `environment` section with your own credentials and settings.**

```yaml
version: '3.8'

services:
  masto-rss:
    # Use the pre-built image from Docker Hub
    image: doorknob2947/masto-rss-advanced:latest
    container_name: masto-rss-bot
    restart: unless-stopped
    volumes:
      # This volume persists the history of posted links
      - ./state:/state
    environment:
      # --- Mastodon API Credentials (Required) ---
      - MASTODON_CLIENT_ID=YOUR_CLIENT_KEY_HERE
      - MASTODON_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
      - MASTODON_ACCESS_TOKEN=YOUR_ACCESS_TOKEN_HERE
      - MASTODON_INSTANCE_URL=[https://mastodon.social](https://mastodon.social)

      # --- RSS Feed Configuration (Required) ---
      - RSS_FEED_URL=[https://www.theverge.com/rss/index.xml](https://www.theverge.com/rss/index.xml)

      # --- Bot Behavior (Optional) ---
      - CHECK_INTERVAL=3600 # Time in seconds between checks (e.g., 1 hour)
      - MAX_HISTORY_SIZE=500 # Max number of posted links to remember
      - TOOT_VISIBILITY=public # public, unlisted, private, or direct

      # --- Toot Content (Optional) ---
      - MASTO_RSS_HASHTAGS="news tech python" # Space-separated list of hashtags
      - TOOT_TEMPLATE='{title}\n\n{link}\n\n{hashtags}'

      # --- System (Do not change) ---
      - PYTHONUNBUFFERED=1
```

### 3. Environment Variables

All configuration is handled through the `environment` section in your `docker-compose.yml` file.

| Variable                 | Description                                                              | Example                                             |
| ------------------------ | ------------------------------------------------------------------------ | --------------------------------------------------- |
| `MASTODON_CLIENT_ID`     | Your Mastodon application's Client Key.                                  | `abc...`                                            |
| `MASTODON_CLIENT_SECRET` | Your Mastodon application's Client Secret.                               | `def...`                                            |
| `MASTODON_ACCESS_TOKEN`  | Your Mastodon application's Access Token.                                | `ghi...`                                            |
| `MASTODON_INSTANCE_URL`  | The base URL of your Mastodon instance.                                  | `https://mastodon.social`                           |
| `RSS_FEED_URL`           | The full URL of the RSS feed you want to monitor.                        | `https://www.theverge.com/rss/index.xml`            |
| `CHECK_INTERVAL`         | (Optional) The time in seconds between checks.                           | `3600` (for 1 hour)                                 |
| `MASTO_RSS_HASHTAGS`     | (Optional) A space-separated list of hashtags to add to each post.       | `news tech python`                                  |
| `MAX_HISTORY_SIZE`       | (Optional) The maximum number of post URLs to remember.                  | `500`                                               |
| `TOOT_VISIBILITY`        | (Optional) The visibility of the toot (`public`, `unlisted`, `private`, `direct`). | `public`                                            |
| `TOOT_TEMPLATE`          | (Optional) A string to format the toot. See "Customizing the Toot Format" below. | `'{title}\n\n{link}\n\n{hashtags}'`                 |
| `PYTHONUNBUFFERED`       | Should be kept at `1` to ensure logs appear in real-time in Docker.      | `1`                                                 |

### 4. Customizing the Toot Format

You can change the layout of your posts using the `TOOT_TEMPLATE` variable. Use the following placeholders:

* `{title}`: The title of the RSS entry.
* `{link}`: The URL of the RSS entry.
* `{hashtags}`: The configured hashtags.

**Examples in `docker-compose.yml`:**

* **Compact Format:**
    ```yaml
    - TOOT_TEMPLATE='{title} - {link} {hashtags}'
    ```
* **Personalized Format:**
    ```yaml
    - TOOT_TEMPLATE='New on the blog: {title}\nRead it here: {link}\n\n{hashtags}'
    ```

## Running the Bot

1.  **Create the `state` directory.** This is required for the bot to remember which links it has already posted.
    ```bash
    mkdir ./state
    ```

2.  **Start the container** in detached (background) mode:
    ```bash
    docker-compose up -d
    ```

The bot is now running!

## Managing the Bot

* **View logs in real-time:**
    ```bash
    docker-compose logs -f
    ```

* **Stop the container:**
    ```bash
    docker-compose down
    ```

* **Restart the container:**
    ```bash
    docker-compose restart
    ```

## Updating the Bot

To update to the latest version of the image from Docker Hub:

1.  **Pull the latest image:**
    ```bash
    docker-compose pull
    ```
2.  **Restart the container** to apply the update:
    ```bash
    docker-compose up -d
    ```

## Acknowledgements

* This project is heavily inspired by and based on the original [masto-rss](https://github.com/piko-system/masto-rss). This version aims to add more robustness, flexibility, and ease of deployment using modern practices.
* The Python script, Docker configuration, and this README were written and modified with the assistance of AI.
