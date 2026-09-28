"""Redis client with a safe optional fallback."""
from __future__ import annotations
import os
try:
    from redis.asyncio import Redis
except ImportError:  # optional dependency
    Redis = None

_client: Redis | None = None

def enabled() -> bool:
    return bool(os.getenv("REDIS_URL", "").strip()) and Redis is not None

def get() -> Redis:
    global _client
    if not enabled():
        raise RuntimeError("Redis is not enabled")
    if _client is None:
        _client = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    return _client

async def close() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None


async def ping() -> bool:
    """Return whether configured Redis is reachable."""
    if not enabled():
        return False
    try:
        from redis.asyncio import Redis
        client = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        try:
            return bool(await client.ping())
        finally:
            await client.aclose()
    except Exception:
        return False
