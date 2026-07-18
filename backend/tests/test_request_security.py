import asyncio

import pytest

from src.middleware.request_security import RequestBoundaryMiddleware, _valid_host


pytestmark = pytest.mark.security


@pytest.mark.parametrize("host", ["localhost:8000", "api.example.com", "127.0.0.1", "[::1]:8000"])
def test_valid_host_authorities(host):
    assert _valid_host(host)


@pytest.mark.parametrize("host", ["", "example.com/api", "example.com\\share", "user@example.com", "bad host"])
def test_ambiguous_host_authorities_are_rejected(host):
    assert not _valid_host(host)


def _invoke(scope, messages, max_body_bytes=16):
    sent = []

    async def app(_scope, receive, send):
        while True:
            message = await receive()
            if not message.get("more_body"):
                break
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    asyncio.run(RequestBoundaryMiddleware(app, max_body_bytes=max_body_bytes)(scope, receive, send))
    return sent


def test_non_slash_request_target_is_rejected_before_routing():
    sent = _invoke(
        {"type": "http", "raw_path": b"@attacker.invalid", "headers": [(b"host", b"localhost")]},
        [{"type": "http.request", "body": b"", "more_body": False}],
    )
    assert sent[0]["status"] == 400


def test_declared_and_streamed_body_limits_are_enforced():
    declared = _invoke(
        {
            "type": "http", "raw_path": b"/api", "headers": [
                (b"host", b"localhost"), (b"content-length", b"17"),
            ],
        },
        [{"type": "http.request", "body": b"", "more_body": False}],
    )
    assert declared[0]["status"] == 413

    streamed = _invoke(
        {"type": "http", "raw_path": b"/api", "headers": [(b"host", b"localhost")]},
        [
            {"type": "http.request", "body": b"1234567890", "more_body": True},
            {"type": "http.request", "body": b"1234567890", "more_body": False},
        ],
    )
    assert streamed[-2]["status"] == 413
