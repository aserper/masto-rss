# Masto-RSS Advanced Bot

A flexible and robust Python script to automatically post the latest entry from an RSS feed to Mastodon, designed to run continuously in a Docker container.

This project is based on the original concept of [masto-rss](https://github.com/piko-system/masto-rss) but has been significantly rewritten and extended with modern features for stability and customization.

## Features

* **Posts Only the Latest Item**: Checks an RSS feed periodically and posts only the single most recent entry, preventing feed spam.
* **Prevents Duplicates**: Keeps a history of posted items to ensure the same link is never posted twice.
* **History Limit**: The history file is automatically pruned to a configurable size (`MAX_HISTORY_SIZE`) to prevent it from growing indefinitely.
* **Custom Toot Format**: Fully customize the look of your posts using a template string with placeholders (`{title}`, `{link}`, `{hashtags}`).
* **Hashtag Support**: Automatically append a configurable list of hashtags to every post.
* **Dockerized**: Comes with a `Dockerfile` and `docker-compose.yml` for easy, reliable, and isolated deployment.
* **Robust Error Handling**: Designed to run forever, it handles connection errors to the RSS feed or Mastodon gracefully without crashing.

## Setup & Configuration

The recommended way to run this bot is by using Docker and Docker Compose.

### 1. Prerequisites

* Docker and Docker Compose installed on your system.
* A Mastodon account and an application set up in `Preferences > Development`. You will need the `Client Key`, `Client Secret`, and `Access Token`.

### 2. Create the Project Files

Create a directory for your project and place the following files inside:

1.  `masto-rss.py` (The Python script)
2.  `Dockerfile`
3.  `requirements.txt`
4.  `docker-compose.yml`

### 3. Configure Environment Variables

All configuration is handled through the `docker-compose.yml` file. Open it and edit the `environment` section with your own details.

| Variable                 | Description                                                                                | Example                                          |
| :----------------------- | :----------------------------------------------------------------------------------------- | :----------------------------------------------- |
| `MASTODON_CLIENT_ID`     | Your Mastodon application's Client Key.                                                    | `abc...`                                         |
| `MASTODON_CLIENT_SECRET` | Your Mastodon application's Client Secret.                                                 | `def...`                                         |
| `MASTODON_ACCESS_TOKEN`  | Your Mastodon application's Access Token.                                                  | `ghi...`                                         |
| `MASTODON_INSTANCE_URL`  | The base URL of your Mastodon instance.                                                    | `https://mastodon.social`                        |
| `RSS_FEED_URL`           | The full URL of the RSS feed you want to monitor.                                          | `https://www.theverge.com/rss/index.xml`         |
| `CHECK_INTERVAL`         | **(Optional)** The time in seconds between checks.                                         | `3600` (for 1 hour)                              |
| `MASTO_RSS_HASHTAGS`     | **(Optional)** A space-separated list of hashtags to add to each post.                     | `news tech python`                               |
| `MAX_HISTORY_SIZE`       | **(Optional)** The maximum number of post URLs to remember.                                | `500`                                            |
| `TOOT_VISIBILITY`        | **(Optional)** The visibility of the toot (`public`, `unlisted`, `private`, `direct`).     | `public`                                         |
| `TOOT_TEMPLATE`          | **(Optional)** A string to format the toot. See "Customizing the Toot Format" below.       | `'{title}\n\n{link}\n\n{hashtags}'`               |
| `PYTHONUNBUFFERED`       | Should be kept at `1` to ensure logs appear in real-time in Docker.                        | `1`                                              |

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

1.  Make sure you have configured your `docker-compose.yml` file correctly.
2.  Create the state directory from your terminal:
    ```bash
    mkdir ./state
    ```
3.  Start the container in detached mode:
    ```bash
    docker-compose up -d
    ```
The bot is now running!

### Managing the Container

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

* **Update the script and rebuild the image:**
    ```bash
    docker-compose up -d --build
    ```

## Acknowledgements

This project is heavily inspired by and based on the original [masto-rss](https://github.com/piko-system/masto-rss). This version aims to add more robustness, flexibility, and ease of deployment using modern practices.

The Python script, Docker configuration, and this README were written and modified with the assistance of AI.
