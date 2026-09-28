"""Durable job-queue primitives. Uses Redis-backed ARQ when configured."""
from __future__ import annotations
import os
from typing import Any


def enabled() -> bool:
    return bool(os.getenv("REDIS_URL", "").strip())

async def enqueue(function: str, **kwargs: Any) -> str | None:
    if not enabled():
        return None
    from arq import create_pool
    from arq.connections import RedisSettings
    settings = RedisSettings.from_dsn(os.environ["REDIS_URL"])
    pool = await create_pool(settings)
    try:
        job = await pool.enqueue_job(function, **kwargs)
        return job.job_id if job else None
    finally:
        await pool.close()
