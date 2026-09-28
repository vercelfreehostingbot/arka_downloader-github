"""Security helpers for the health/control HTTP surface."""
from __future__ import annotations
import os
from aiohttp import web

@web.middleware
async def security_headers(request: web.Request, handler):
    response = await handler(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response

def metrics_token_ok(request: web.Request) -> bool:
    expected = os.getenv("METRICS_TOKEN", "").strip()
    return not expected or request.headers.get("Authorization") == f"Bearer {expected}"
