import asyncio
from unittest.mock import patch, AsyncMock
import pytest
import multi_platform_streamer as mps
import aiohttp

class DummyResponse:
    def __init__(self, data):
        self._data = data
    async def json(self):
        return self._data
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass

def test_fetch_reddit():
    async def _run():
        data = {"data": {"children": [{"data": {"title": "post", "created_utc": 1}}]}}
        with patch("aiohttp.ClientSession.get", return_value=DummyResponse(data)):
            async with aiohttp.ClientSession() as session:
                posts = await mps.fetch_reddit("test", session)
        assert posts[0]["platform"] == "reddit"
    asyncio.run(_run())
def test_stream_posts_aggregates():
    async def _run():
        async def fake_fetch_reddit(sub, session):
            return [{"platform": "reddit", "text": "r", "timestamp": "t"}]
        async def fake_fetch_twitter(q, token, session):
            return [{"platform": "twitter", "text": "tw", "timestamp": "t"}]
        async def fake_fetch_discord(c, token, session):
            return [{"platform": "discord", "text": "d", "timestamp": "t"}]

        with patch.object(mps, "fetch_reddit", side_effect=fake_fetch_reddit), \
             patch.object(mps, "fetch_twitter", side_effect=fake_fetch_twitter), \
             patch.object(mps, "fetch_discord", side_effect=fake_fetch_discord):
            config = {
                "reddit": ["sub"],
                "twitter": ["q"],
                "discord": ["123"],
                "twitter_token": "a",
                "discord_token": "b",
            }
            gen = mps.stream_posts(config, interval_seconds=0, run_duration_seconds=0.1)
            results = []
            async for batch in gen:
                results.extend(batch)
            assert len(results) >= 3
    asyncio.run(_run())

def test_stream_and_store_posts():
    async def _run():
        async def fake_stream_posts(config, interval_seconds=0, run_duration_seconds=0.1):
            yield [{"platform": "reddit", "text": "r", "timestamp": "t"}]

        from unittest.mock import MagicMock
        db = MagicMock()

        with patch.object(mps, "stream_posts", fake_stream_posts):
            config = {}
            gen = mps.stream_and_store_posts(config, db, interval_seconds=0, run_duration_seconds=0.1)
            results = []
            async for batch in gen:
                results.extend(batch)
            db.bulk_insert_posts.assert_called()
            assert len(results) == 1
    asyncio.run(_run())
