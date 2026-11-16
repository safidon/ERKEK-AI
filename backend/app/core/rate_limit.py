"""
Rate limiting.

Әр клиент (IP) үшін sliding-window лимит. Қосымша тәуелділік
қажет емес: санауыштар процесс жадында сақталады, сондықтан
backend бір uvicorn worker-мен іске қосылуы керек
(Docker конфигурациясы солай жасалған). Бірнеше worker немесе
бірнеше сервер керек болса — Redis негізіндегі лимитке ауысу керек.
"""

import json
import os
import threading
import time
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateRule:
    name: str
    prefixes: tuple[str, ...]
    limit: int
    window_seconds: int


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


# Ретімен тексеріледі: бірінші сәйкес келген ереже қолданылады.
DEFAULT_RULES: tuple[RateRule, ...] = (
    RateRule(
        "auth",
        (
            "/auth/login",
            "/auth/register",
            "/auth/forgot-password",
            "/auth/reset-password",
            "/auth/delete-account",
            "/auth/google",
        ),
        _env_int("RATE_LIMIT_AUTH_PER_MINUTE", 10),
        60,
    ),
    RateRule(
        "chat",
        ("/chat",),
        _env_int("RATE_LIMIT_CHAT_PER_MINUTE", 20),
        60,
    ),
    RateRule(
        "default",
        ("/",),
        _env_int("RATE_LIMIT_DEFAULT_PER_MINUTE", 120),
        60,
    ),
)

# Бұл жолдар лимитке кірмейді (мониторинг жиі тексереді).
# /telegram/webhook: Telegram серверлері бірнеше IP-ден келеді,
# сұраныс құпия token-мен тексеріледі; күндік лимит бәрібір жұмыс істейді.
EXEMPT_PATHS = ("/health", "/telegram/webhook")


class RateLimiter:
    def __init__(self, rules: tuple[RateRule, ...] = DEFAULT_RULES):
        self.rules = rules
        self._hits: dict[tuple[str, str], deque[float]] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()

    def match(self, path: str) -> RateRule | None:
        if path.startswith(EXEMPT_PATHS):
            return None

        for rule in self.rules:
            if path.startswith(rule.prefixes):
                return rule

        return None

    def hit(self, rule: RateRule, client: str) -> float | None:
        """
        Сұранысты тіркейді. Лимит асса — қанша секундтан кейін
        қайталауға болатынын қайтарады, әйтпесе None.
        """

        now = time.monotonic()
        key = (rule.name, client)

        with self._lock:
            self._cleanup(now)

            window = self._hits.setdefault(key, deque())
            cutoff = now - rule.window_seconds

            while window and window[0] <= cutoff:
                window.popleft()

            if len(window) >= rule.limit:
                return max(window[0] + rule.window_seconds - now, 1.0)

            window.append(now)
            return None

    def _cleanup(self, now: float) -> None:
        # Жады өсіп кетпес үшін бос терезелерді анда-санда өшіреміз.
        if now - self._last_cleanup < 60:
            return

        self._last_cleanup = now
        longest = max(rule.window_seconds for rule in self.rules)

        for key in list(self._hits):
            window = self._hits[key]

            if not window or window[-1] <= now - longest:
                del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def _client_ip(scope) -> str:
    # uvicorn --proxy-headers қосылғанда client нағыз IP болады
    # (reverse proxy X-Forwarded-For арқылы береді).
    client = scope.get("client")
    return client[0] if client else "unknown"


class RateLimitMiddleware:
    """Pure ASGI middleware (streaming жауаптарды бұзбайды)."""

    def __init__(self, app, limiter: RateLimiter, enabled: bool = True):
        self.app = app
        self.limiter = limiter
        self.enabled = enabled

    async def __call__(self, scope, receive, send):
        if (
            not self.enabled
            or scope["type"] != "http"
            or scope.get("method") == "OPTIONS"
        ):
            await self.app(scope, receive, send)
            return

        rule = self.limiter.match(scope.get("path", ""))

        if rule is not None:
            retry_after = self.limiter.hit(rule, _client_ip(scope))

            if retry_after is not None:
                body = json.dumps(
                    {
                        "detail": (
                            "Сұраныс тым көп. "
                            "Біраз уақыттан кейін қайталап көр."
                        )
                    },
                    ensure_ascii=False,
                ).encode("utf-8")

                await send(
                    {
                        "type": "http.response.start",
                        "status": 429,
                        "headers": [
                            (b"content-type", b"application/json; charset=utf-8"),
                            (b"retry-after", str(int(retry_after + 0.999)).encode()),
                            (b"content-length", str(len(body)).encode()),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": body})
                return

        await self.app(scope, receive, send)
