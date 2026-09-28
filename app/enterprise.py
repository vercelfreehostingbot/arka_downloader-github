"""Enterprise runtime services for Arka Downloader.

Optional integrations are enabled by environment variables and fail closed so
that the existing Telegram bot remains usable when an observability backend is
not configured.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from contextlib import suppress
from typing import Optional

from aiohttp import web

from infra.security.headers import metrics_token_ok, security_headers
from infra.db import postgres
from infra.cache import redis as redis_infra

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    Counter = Gauge = None
    generate_latest = None

try:
    import sentry_sdk
except Exception:  # pragma: no cover
    sentry_sdk = None

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover
    Redis = None

log = logging.getLogger("arka.enterprise")

if Counter:
    REQUESTS = Counter("arka_requests_total", "Telegram/runtime requests", ["kind"])
    DOWNLOADS = Counter("arka_downloads_total", "Downloads by final state", ["status"])
    ACTIVE_JOBS = Gauge("arka_active_jobs", "Currently active download jobs")
    HEALTH = Gauge("arka_health", "Overall process health")
else:
    REQUESTS = DOWNLOADS = ACTIVE_JOBS = HEALTH = None


class EnterpriseRuntime:
    def __init__(self) -> None:
        self.redis: Optional[Redis] = None
        self.site: Optional[web.TCPSite] = None
        self.runner: Optional[web.AppRunner] = None
        self.started_at = time.time()

    async def start(self) -> None:
        self._init_sentry()
        await self._init_redis()
        postgres.init()
        await self._start_http()
        if HEALTH:
            HEALTH.set(1)
        log.info("enterprise runtime started")

    async def stop(self) -> None:
        if HEALTH:
            HEALTH.set(0)
        if self.site:
            with suppress(Exception):
                await self.site.stop()
        if self.runner:
            with suppress(Exception):
                await self.runner.cleanup()
        if self.redis:
            with suppress(Exception):
                await self.redis.aclose()
        with suppress(Exception):
            await postgres.close()
        log.info("enterprise runtime stopped")

    def _init_sentry(self) -> None:
        dsn = os.getenv("SENTRY_DSN", "").strip()
        if not dsn or not sentry_sdk:
            return
        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("APP_ENV", "production"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_RATE", "0.05")),
            send_default_pii=False,
        )
        log.info("Sentry enabled")

    async def _init_redis(self) -> None:
        url = os.getenv("REDIS_URL", "").strip()
        if not url or not Redis:
            return
        try:
            self.redis = Redis.from_url(url, decode_responses=True)
            await self.redis.ping()
            log.info("Redis connected")
        except Exception as exc:
            self.redis = None
            log.warning("Redis unavailable; continuing without it: %s", exc)

    async def _start_http(self) -> None:
        app = web.Application(middlewares=[security_headers])
        app.router.add_get("/health", self.health)
        app.router.add_get("/ready", self.ready)
        app.router.add_get("/metrics", self.metrics)
        self.runner = web.AppRunner(app, access_log=None)
        await self.runner.setup()
        host = os.getenv("HEALTH_HOST", "0.0.0.0")
        try:
            port = int(os.getenv("HEALTH_PORT", "8090"))
        except (TypeError, ValueError):
            port = 8090

        # Never let an unrelated process on the configured health port kill
        # the Telegram bot. Try the configured port first, then a small
        # deterministic range of fallback ports.
        last_error = None
        for candidate in [port] + [p for p in range(8090, 8191) if p != port]:
            try:
                self.site = web.TCPSite(self.runner, host, candidate)
                await self.site.start()
                if candidate != port:
                    log.warning(
                        "health port %s is busy; using fallback port %s",
                        port, candidate)
                log.info("health server listening on %s:%s", host, candidate)
                return
            except OSError as exc:
                last_error = exc
                if self.site:
                    with suppress(Exception):
                        await self.site.stop()
                self.site = None
        raise last_error if last_error else OSError("no health port available")

    async def health(self, _: web.Request) -> web.Response:
        payload = {"status": "ok", "uptime": round(time.time() - self.started_at, 2)}
        return web.json_response(payload)

    async def ready(self, _: web.Request) -> web.Response:
        pg_required = bool(os.getenv("DATABASE_URL", "").strip())
        redis_required = bool(os.getenv("REDIS_REQUIRED", "0") == "1")
        pg_ok = await postgres.ping() if pg_required else True
        redis_ok = await redis_infra.ping() if redis_required else True
        ready = pg_ok and redis_ok
        payload = {
            "status": "ready" if ready else "not_ready",
            "postgres": "ok" if pg_ok else "unavailable",
            "redis": "ok" if redis_ok else "unavailable",
        }
        return web.json_response(payload, status=200 if ready else 503)

    async def metrics(self, request: web.Request) -> web.Response:
        if not metrics_token_ok(request):
            return web.json_response({"status": "forbidden"}, status=403)
        if not generate_latest:
            return web.json_response({"metrics": "disabled"})
        return web.Response(body=generate_latest(), content_type=CONTENT_TYPE_LATEST.split(";")[0])


runtime = EnterpriseRuntime()
