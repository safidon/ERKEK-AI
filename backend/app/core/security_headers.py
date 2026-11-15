"""
Security headers барлық API жауаптарына қосылады.
"""

BASE_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
    (b"cross-origin-opener-policy", b"same-origin"),
]

HSTS_HEADER = (
    b"strict-transport-security",
    b"max-age=31536000; includeSubDomains",
)


class SecurityHeadersMiddleware:
    """Pure ASGI middleware (streaming жауаптарды бұзбайды)."""

    def __init__(self, app, hsts: bool = False):
        self.app = app
        self.headers = BASE_HEADERS + ([HSTS_HEADER] if hsts else [])

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                existing = {name.lower() for name, _ in message.get("headers", [])}
                extra = [
                    header for header in self.headers
                    if header[0] not in existing
                ]
                message["headers"] = list(message.get("headers", [])) + extra

            await send(message)

        await self.app(scope, receive, send_with_headers)
