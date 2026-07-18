"""ASGI request-boundary controls for framework advisories and body limits."""

import json
import os
import re
from typing import Awaitable, Callable, Dict, Optional


_HOST_PATTERN = re.compile(
    r"^(?:\[[0-9a-fA-F:]+\]|[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?)(?::[0-9]{1,5})?$"
)


class RequestBoundaryMiddleware:
    """Reject ambiguous authority/path values and enforce a streaming body cap."""

    def __init__(self, app, max_body_bytes: Optional[int] = None):
        self.app = app
        self.max_body_bytes = max_body_bytes or int(os.getenv("MAX_REQUEST_BODY_BYTES", str(5 * 1024 * 1024)))

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        raw_path = scope.get("raw_path") or str(scope.get("path") or "").encode("utf-8", "replace")
        headers: Dict[bytes, bytes] = dict(scope.get("headers") or [])
        host = headers.get(b"host", b"").decode("latin-1", "replace")
        if not raw_path.startswith(b"/") or not _valid_host(host):
            await _error_response(send, 400, "invalid_request_target")
            return
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    await _error_response(send, 413, "request_body_too_large")
                    return
            except ValueError:
                await _error_response(send, 400, "invalid_content_length")
                return

        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body") or b"")
                if received > self.max_body_bytes:
                    raise _BodyLimitExceeded
            return message

        try:
            await self.app(scope, bounded_receive, send)
        except _BodyLimitExceeded:
            await _error_response(send, 413, "request_body_too_large")


class _BodyLimitExceeded(Exception):
    pass


def _valid_host(host: str) -> bool:
    if not host or any(character in host for character in ("/", "\\", "@", "\r", "\n", "\t", " ")):
        return False
    return bool(_HOST_PATTERN.fullmatch(host))


async def _error_response(send: Callable[[dict], Awaitable[None]], status: int, code: str) -> None:
    body = json.dumps({"success": False, "error": {"code": code}}).encode()
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
    })
    await send({"type": "http.response.body", "body": body})
