#!/usr/bin/env python3
"""
Streams live Reddit comments from r/news and publishes each JSON payload
to Kafka topic 'topic1'.
Requires two env vars:
  REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
Get them from https://www.reddit.com/prefs/apps
"""
import os, json, time, praw
from kafka import KafkaProducer

REDDIT = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    user_agent="cs6350-realtime-ner-pipeline"
)
SUBREDDIT = "news"
PRODUCER = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print(f"→ Streaming r/{SUBREDDIT} comments into Kafka topic1")
for c in REDDIT.subreddit(SUBREDDIT).stream.comments(skip_existing=True):
    msg = {
        "body": c.body,
        "author": str(c.author),
        "created_utc": c.created_utc,
        "id": c.id,
        "subreddit": SUBREDDIT
    }
    PRODUCER.send("topic1", msg)
    time.sleep(0.1)           # small throttle so local broker stays happy
