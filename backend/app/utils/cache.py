"""Redis helper functions — async and sync (for Celery workers)."""
import json
import redis as sync_redis
import redis.asyncio as aioredis
from app.config import settings

_async_pool = None
_sync_client = None


async def get_redis() -> aioredis.Redis:
    global _async_pool
    if _async_pool is None:
        _async_pool = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _async_pool


def _get_sync_redis() -> sync_redis.Redis:
    global _sync_client
    if _sync_client is None:
        _sync_client = sync_redis.from_url(settings.redis_url, decode_responses=True)
    return _sync_client


# Async helpers
async def set_json(key: str, value: dict, ttl: int = 3600):
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))


async def get_json(key: str) -> dict | None:
    r = await get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw else None


# Sync helpers (for Celery workers which run synchronous tasks)
def set_json_sync(key: str, value: dict, ttl: int = 3600):
    r = _get_sync_redis()
    r.setex(key, ttl, json.dumps(value))


def get_json_sync(key: str) -> dict | None:
    r = _get_sync_redis()
    raw = r.get(key)
    return json.loads(raw) if raw else None


def push_event_sync(task_id: str, event: dict):
    """Append a progress event to a Redis list so the WebSocket can relay it."""
    r = _get_sync_redis()
    key = f"events:{task_id}"
    r.rpush(key, json.dumps(event))
    r.expire(key, 3600)
