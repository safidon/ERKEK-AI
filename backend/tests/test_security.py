from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import (
    RateLimiter,
    RateLimitMiddleware,
    RateRule,
)
from app.core.security_headers import SecurityHeadersMiddleware
from app.database import get_database_type
from app.main import app


def _make_app(limit: int) -> FastAPI:
    test_app = FastAPI()

    @test_app.post("/auth/login")
    def login():
        return {"ok": True}

    @test_app.get("/health")
    def health():
        return {"ok": True}

    limiter = RateLimiter(
        rules=(RateRule("auth", ("/auth/login",), limit, 60),)
    )
    test_app.add_middleware(RateLimitMiddleware, limiter=limiter)
    test_app.add_middleware(SecurityHeadersMiddleware, hsts=True)
    return test_app


def test_rate_limit_blocks_after_limit():
    client = TestClient(_make_app(limit=3))

    for _ in range(3):
        assert client.post("/auth/login").status_code == 200

    blocked = client.post("/auth/login")

    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) >= 1
    assert "detail" in blocked.json()


def test_rate_limit_ignores_health_and_options():
    client = TestClient(_make_app(limit=1))

    for _ in range(5):
        assert client.get("/health").status_code == 200

    client.post("/auth/login")

    assert client.options("/auth/login").status_code != 429


def test_rate_limit_is_per_client():
    limiter = RateLimiter(rules=(RateRule("auth", ("/auth",), 1, 60),))
    rule = limiter.rules[0]

    assert limiter.hit(rule, "1.1.1.1") is None
    assert limiter.hit(rule, "2.2.2.2") is None
    assert limiter.hit(rule, "1.1.1.1") is not None


def test_security_headers_present():
    client = TestClient(_make_app(limit=10))
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "max-age" in response.headers["strict-transport-security"]


def test_main_app_health_and_ready():
    client = TestClient(app)

    assert client.get("/health").json()["status"] == "ok"

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == get_database_type()
    assert ready.headers["x-content-type-options"] == "nosniff"
