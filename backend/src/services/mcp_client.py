"""Hand-written MCP stdio client (V1.3 P3, T10).

Implements the minimum MCP stdio surface the Local Tool Runtime needs:
initialize handshake → tools/list → tools/call, over newline-delimited
JSON-RPC 2.0 (the stable stdio framing shared by all official servers).

Deliberately hand-written instead of using the official `mcp` SDK:
the SDK requires Python >= 3.10 while the local dev venv is 3.9, and
the stdio JSON-RPC framing is small and stable. Zero new dependencies;
works against real servers (e.g. @modelcontextprotocol/server-filesystem
via npx) and against a deterministic stub server in tests.

Per-call lifecycle: a fresh server process is spawned per client
instance (connect → operate → close). Correct and stateless; persistent
sessions are a V1.4 optimization once a parallel runtime exists.
"""

import json
import os
import selectors
import subprocess
import time
import uuid
from typing import Any, Dict, List, Optional

MCP_PROTOCOL_VERSION = "2024-11-05"
CLIENT_INFO = {"name": "modelgate-agent-studio", "version": "1.0"}


class MCPClientError(RuntimeError):
    """Raised for spawn failures, protocol errors and timeouts."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class MCPStdioClient:
    """Spawn an MCP server over stdio and speak JSON-RPC 2.0 with it."""

    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        self.command = command
        self.args = args or []
        self.timeout = timeout
        self._process: Optional[subprocess.Popen] = None
        self._selector: Optional[selectors.DefaultSelector] = None
        self._buffer = ""
        self._next_id = 0
        # Child env: inherit the parent env so node/python servers find their
        # runtime, then overlay the server-specific secrets.
        self._child_env = {**os.environ, **(env or {})}

    # -- lifecycle ------------------------------------------------------ #

    def __enter__(self) -> "MCPStdioClient":
        self.connect()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def connect(self) -> None:
        try:
            self._process = subprocess.Popen(
                [self.command, *self.args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                env=self._child_env,
                bufsize=1,
            )
        except (OSError, FileNotFoundError) as exc:
            raise MCPClientError("spawn_failed", f"cannot spawn {self.command!r}: {exc}") from exc
        self._selector = selectors.DefaultSelector()
        self._selector.register(self._process.stdout, selectors.EVENT_READ)

    def close(self) -> None:
        if self._selector:
            self._selector.close()
            self._selector = None
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except (subprocess.TimeoutExpired, OSError):
                self._process.kill()
            self._process = None

    # -- protocol ------------------------------------------------------- #

    def _send(self, payload: Dict[str, Any]) -> None:
        assert self._process and self._process.stdin
        line = json.dumps(payload, ensure_ascii=False)
        try:
            self._process.stdin.write(line + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise MCPClientError("broken_pipe", f"server closed stdin: {exc}") from exc

    def _recv_response(self, want_id: str, deadline: float) -> Dict[str, Any]:
        """Read lines until the JSON-RPC response with `want_id` arrives.
        Notifications (no id) and unrelated requests are skipped."""
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MCPClientError("timeout", f"no response for request {want_id} within {self.timeout}s")
            line = self._readline(remaining)
            if line is None:
                if self._process and self._process.poll() is not None:
                    raise MCPClientError("server_exited", f"server exited with code {self._process.returncode}")
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue  # tolerate stray non-JSON output on stdout
            if not isinstance(message, dict):
                continue
            if message.get("id") != want_id:
                continue  # notification or unrelated message
            if "error" in message:
                error = message["error"] or {}
                raise MCPClientError(
                    "server_error",
                    str(error.get("message", "unknown MCP error")),
                )
            return message.get("result") or {}

    def _readline(self, timeout: float) -> Optional[str]:
        """Read one newline-terminated line within `timeout` seconds.
        Returns None on poll timeout (caller re-checks process liveness
        and its own deadline)."""
        assert self._selector is not None
        while "\n" not in self._buffer:
            events = self._selector.select(timeout=timeout)
            if not events:
                return None
            for key, _ in events:
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    continue  # spurious wakeup; poll will report EOF next round
                self._buffer += chunk.decode("utf-8", errors="replace")
            if self._process and self._process.poll() is not None and "\n" not in self._buffer:
                # Process died; drain whatever remains then report via caller.
                raise MCPClientError("server_exited", f"server exited with code {self._process.returncode}")
        line, self._buffer = self._buffer.split("\n", 1)
        return line

    # -- public API ------------------------------------------------------ #

    def _rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._next_id += 1
        request_id = f"mg-{self._next_id}-{uuid.uuid4().hex[:8]}"
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        deadline = time.monotonic() + self.timeout
        self._send(payload)
        return self._recv_response(request_id, deadline)

    def _notify(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        payload: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def initialize(self) -> Dict[str, Any]:
        result = self._rpc("initialize", {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO,
        })
        self._notify("notifications/initialized")
        return result

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return the server's tools as [{name, description, input_schema}]."""
        self.initialize()
        result = self._rpc("tools/list")
        tools = result.get("tools", [])
        return [
            {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema") or {"type": "object", "properties": {}},
            }
            for tool in tools
            if isinstance(tool, dict) and tool.get("name")
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool; returns {'content': str, 'is_error': bool, 'raw': result}."""
        self.initialize()
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        content_parts = []
        for block in result.get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text":
                content_parts.append(str(block.get("text", "")))
        return {
            "content": "\n".join(content_parts),
            "is_error": bool(result.get("isError", False)),
            "raw": result,
        }
