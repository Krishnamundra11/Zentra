"""Redis helper functions — async and sync (for Celery workers)."""
import json
import ssl
import redis as sync_redis
import redis.asyncio as aioredis
from app.config import settings

_async_pool = None
_sync_client = None


def _clean_url_and_kwargs(url: str, is_async: bool = False):
    """Strip celery-specific ssl params and return standard redis kwargs."""
    kwargs = {}
    if "rediss://" in url:
        kwargs["ssl_cert_reqs"] = "none" if is_async else ssl.CERT_NONE
    clean_url = url.split("?")[0]
    return clean_url, kwargs


async def get_redis() -> aioredis.Redis:
    global _async_pool
    if _async_pool is None:
        url, kwargs = _clean_url_and_kwargs(settings.redis_url, is_async=True)
        _async_pool = aioredis.from_url(url, decode_responses=True, **kwargs)
    return _async_pool


def _get_sync_redis() -> sync_redis.Redis:
    global _sync_client
    if _sync_client is None:
        url, kwargs = _clean_url_and_kwargs(settings.redis_url, is_async=False)
        _sync_client = sync_redis.from_url(url, decode_responses=True, **kwargs)
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
