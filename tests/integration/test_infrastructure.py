import os
import pytest


def test_optional_backends_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    from infra.db.postgres import enabled as pg_enabled
    from infra.cache.redis import enabled as redis_enabled
    assert not pg_enabled()
    assert not redis_enabled()


def test_security_headers():
    from infra.security.headers import metrics_token_ok
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("METRICS_TOKEN", "secret")
    from aiohttp.test_utils import make_mocked_request
    req = make_mocked_request("GET", "/metrics", headers={"Authorization": "Bearer secret"})
    assert metrics_token_ok(req)
    monkeypatch.undo()
