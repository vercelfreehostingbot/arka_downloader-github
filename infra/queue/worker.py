"""ARQ worker settings for scalable download workloads."""
from __future__ import annotations

import os
from typing import Any


def _redis_settings() -> Any:
    dsn = os.getenv("REDIS_URL", "").strip()
    if not dsn:
        return None
    try:
        from arq.connections import RedisSettings
    except ImportError as exc:
        raise RuntimeError("ARQ is required when REDIS_URL/QUEUE_MODE=arq is enabled") from exc
    return RedisSettings.from_dsn(dsn)


async def download_job(ctx: Any, job_id: str, **payload: Any) -> dict[str, Any]:
    # Stable boundary for moving a job to a remote worker.
    return {"job_id": job_id, "payload": payload, "status": "accepted"}


class WorkerSettings:
    functions = [download_job]
    redis_settings = _redis_settings()
    max_jobs = max(1, int(os.getenv("QUEUE_MAX_JOBS", "4")))
    job_timeout = max(60, int(os.getenv("QUEUE_JOB_TIMEOUT", "3600")))
    keep_result = max(60, int(os.getenv("QUEUE_KEEP_RESULT", "3600")))
