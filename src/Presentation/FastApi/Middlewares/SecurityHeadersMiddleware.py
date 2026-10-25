from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    _SECURITY_HEADERS: tuple[tuple[bytes, bytes], ...] = (
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"x-xss-protection", b"0"),
        (b"referrer-policy", b"no-referrer"),
        (b"permissions-policy", b"geolocation=(), microphone=(), camera=()"),
        (
            b"content-security-policy",
            b"default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data:; font-src 'self' data:; connect-src 'self'",
        ),
    )
    _HSTS_HEADER: tuple[bytes, bytes] = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers: list[tuple[bytes, bytes]] = message.setdefault("headers", [])
                existing_headers = {key.lower() for key, _ in headers}

                for key, value in self._SECURITY_HEADERS:
                    if key not in existing_headers:
                        headers.append((key, value))

                if self._should_add_hsts(scope) and self._HSTS_HEADER[0] not in existing_headers:
                    headers.append(self._HSTS_HEADER)

            await send(message)

        await self.app(scope, receive, send_with_security_headers)

    @staticmethod
    def _should_add_hsts(scope: Scope) -> bool:
        if scope.get("scheme") == "https":
            return True

        for key, value in scope.get("headers", []):
            if key.lower() == b"x-forwarded-proto" and value.lower() == b"https":
                return True

        return False
