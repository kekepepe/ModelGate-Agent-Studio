"""V1.3 P3 T10: hand-written MCP stdio client.

Exercised against a deterministic stub server (tests/fixtures) so the
suite stays offline and hermetic; the real @modelcontextprotocol/
server-filesystem is exercised by scripts/e2e-mcp.sh.
"""
import os
import sys

import pytest

from src.services.mcp_client import MCPClientError, MCPStdioClient

STUB_SERVER = os.path.join(os.path.dirname(__file__), "fixtures", "mcp_stub_server.py")


@pytest.fixture
def client():
    with MCPStdioClient(sys.executable, [STUB_SERVER], timeout=10) as client:
        yield client


def test_list_tools_returns_normalized_shape(client):
    tools = client.list_tools()
    names = {tool["name"] for tool in tools}
    assert {"echo", "fail"} <= names
    for tool in tools:
        assert tool["input_schema"]["type"] == "object"


def test_call_tool_echo_roundtrip(client):
    result = client.call_tool("echo", {"message": "hello modelgate"})
    assert result["is_error"] is False
    assert '"message": "hello modelgate"' in result["content"]


def test_call_tool_error_result_is_flagged(client):
    result = client.call_tool("fail", {})
    assert result["is_error"] is True
    assert "stub failure" in result["content"]


def test_call_unknown_tool_raises_server_error(client):
    with pytest.raises(MCPClientError) as exc_info:
        client.call_tool("no_such_tool", {})
    assert exc_info.value.code == "server_error"


def test_spawn_failure_raises_client_error():
    with pytest.raises(MCPClientError) as exc_info:
        with MCPStdioClient("/nonexistent/mcp-server-binary", [], timeout=5):
            pass
    assert exc_info.value.code == "spawn_failed"


def test_timeout_on_silent_server():
    # A server that never answers tools/list must raise a timeout instead of
    # hanging the runtime.
    silent = os.path.join(os.path.dirname(__file__), "fixtures", "mcp_silent_server.py")
    with pytest.raises(MCPClientError) as exc_info:
        with MCPStdioClient(sys.executable, [silent], timeout=1) as client:
            client.list_tools()
    assert exc_info.value.code == "timeout"
