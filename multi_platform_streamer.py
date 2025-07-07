import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, AsyncGenerator
import aiohttp
from setup_logging import setup_logging

logger = setup_logging("multi_stream", log_dir=os.path.join(os.getcwd(), "logs", "social"))

async def fetch_reddit(subreddit: str, session: aiohttp.ClientSession) -> List[Dict]:
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=20"
    headers = {"User-Agent": "sentiment-bot/0.1"}
    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
    except Exception as e:
        logger.error("Reddit fetch error: %s", e)
        return []
    posts = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        timestamp = datetime.utcfromtimestamp(post.get("created_utc", 0)).isoformat()
        posts.append({"platform": "reddit", "text": post.get("title", ""), "timestamp": timestamp})
    return posts

async def fetch_twitter(query: str, bearer_token: str, session: aiohttp.ClientSession) -> List[Dict]:
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {"query": query, "tweet.fields": "created_at", "max_results": 10}
    try:
        async with session.get(url, headers=headers, params=params) as resp:
            data = await resp.json()
    except Exception as e:
        logger.error("Twitter fetch error: %s", e)
        return []
    posts = []
    for tweet in data.get("data", []):
        posts.append({"platform": "twitter", "text": tweet.get("text", ""), "timestamp": tweet.get("created_at", "")})
    return posts

async def fetch_discord(channel_id: str, bot_token: str, session: aiohttp.ClientSession) -> List[Dict]:
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {bot_token}"}
    params = {"limit": 10}
    try:
        async with session.get(url, headers=headers, params=params) as resp:
            data = await resp.json()
    except Exception as e:
        logger.error("Discord fetch error: %s", e)
        return []
    posts = []
    for msg in data:
        posts.append({"platform": "discord", "text": msg.get("content", ""), "timestamp": msg.get("timestamp", "")})
    return posts

async def stream_posts(config: Dict, interval_seconds: int = 60, run_duration_seconds: int = 3600) -> AsyncGenerator[List[Dict], None]:
    start = datetime.now()
    async with aiohttp.ClientSession() as session:
        while (datetime.now() - start).total_seconds() < run_duration_seconds:
            results: List[Dict] = []
            for sub in config.get("reddit", []):
                results.extend(await fetch_reddit(sub, session))
            twitter_token = config.get("twitter_token")
            for query in config.get("twitter", []):
                if twitter_token:
                    results.extend(await fetch_twitter(query, twitter_token, session))
            discord_token = config.get("discord_token")
            for cid in config.get("discord", []):
                if discord_token:
                    results.extend(await fetch_discord(cid, discord_token, session))
            yield results
            await asyncio.sleep(interval_seconds)

async def stream_and_store_posts(config: Dict, db_handler, interval_seconds: int = 60, run_duration_seconds: int = 3600) -> AsyncGenerator[List[Dict], None]:
    """Streams posts and stores them using the provided DatabaseHandler."""
    async for batch in stream_posts(config, interval_seconds, run_duration_seconds):
        if batch:
            rows = [(p["platform"], p["text"], p["timestamp"]) for p in batch]
            try:
                db_handler.bulk_insert_posts(rows)
            except Exception as e:
                logger.error("Failed to save posts: %s", e)
        yield batch
