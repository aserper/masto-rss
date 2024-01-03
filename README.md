# Masto-rss

A simple Mastodon bot written in python that posts updates from an RSS feed to a Mastodon account.
This project is meant to be built to a docker container, so all of the options need to be set as environment variables:

MASTODON_CLIENT_ID = Mastodon  client  ID

MASTODON_CLIENT_SECRET = Mastodon  client  secret

MASTODON_ACCESS_TOKEN = Mastodon  access  token

MASTODON_INSTANCE_URL = Mastodon  instance  URL

RSS_FEED_URL = URL  of  RSS/xml  feed

TOOT_VISIBILITY = 'public', 'unlisted', 'private', or 'direct'

The best way to use this project is by using [its docker container](https://hub.docker.com/r/amitserper/masto-rss)
When using docker, make a bind mount between /state on the container to whatever directory you want on your machine in order to keep the state of the feeds that were already posted
![image](https://github.com/aserper/masto-rss/actions/workflows/masto-rss.yml/badge.svg)
