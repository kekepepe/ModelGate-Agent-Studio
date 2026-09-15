"""MCP server registry service (V1.3 P3, T11+T14).

Register external MCP servers, sync their tool catalogs into
ToolDefinition rows (namespace `mcp__<server>__<tool>`), and keep
health state current. Sync is the single write path for MCP tools;
tools start disabled and require explicit human enablement (D7).
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.tool import MCPToolServer, ToolDefinition
from src.services.mcp_client import MCPClientError, MCPStdioClient


class MCPServiceError(Exception):
    pass


class MCPServerNotFoundError(MCPServiceError):
    pass


def register_server(
    db: Session,
    name: str,
    transport: str,
    command_or_url: str,
    args: Optional[List[str]] = None,
    env_secrets: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Register an MCP server. env_secrets are stored plaintext in the local
    DB (same trust boundary as Model.api_key) and never serialized back."""
    if transport not in {"stdio", "streamable_http"}:
        raise MCPServiceError(f"unsupported MCP transport: {transport}")
    if not name.strip() or not command_or_url.strip():
        raise MCPServiceError("server name and command_or_url are required")
    existing = db.query(MCPToolServer).filter(MCPToolServer.name == name).first()
    if existing:
        raise MCPServiceError(f"an MCP server named '{name}' is already registered")
    server = MCPToolServer(
        id=str(uuid.uuid4()),
        name=name.strip(),
        transport=transport,
        command_or_url=command_or_url.strip(),
        status="active",
    )
    server.set_args(args or [])
    server.set_env_secrets(env_secrets or {})
    db.add(server)
    db.commit()
    db.refresh(server)
    return server.to_dict()


def get_server(db: Session, server_id: str) -> MCPToolServer:
    server = db.query(MCPToolServer).filter(MCPToolServer.id == server_id).first()
    if not server:
        raise MCPServerNotFoundError(f"MCP server '{server_id}' not found")
    return server


def list_servers(db: Session) -> List[Dict[str, Any]]:
    servers = db.query(MCPToolServer).order_by(MCPToolServer.created_at.asc()).all()
    return [server.to_dict() for server in servers]


def set_server_status(db: Session, server_id: str, status: str) -> Dict[str, Any]:
    if status not in {"active", "disabled"}:
        raise MCPServiceError(f"invalid MCP server status: {status}")
    server = get_server(db, server_id)
    server.status = status
    if status == "disabled":
        # A disabled server's tools must not be callable either.
        for tool in db.query(ToolDefinition).filter(ToolDefinition.server_id == server.id).all():
            tool.is_enabled = False
    db.commit()
    db.refresh(server)
    return server.to_dict()


def sync_server(db: Session, server_id: str) -> Dict[str, Any]:
    """Discover the server's tool catalog and upsert ToolDefinition rows.

    Tools are registered as `mcp__<server>__<tool>` with risk_level=high and
    is_enabled=False — enablement is an explicit human decision (D7). Remote
    tools that disappeared are soft-disabled locally (D8 degradation).
    """
    server = get_server(db, server_id)
    if server.transport != "stdio":
        raise MCPServiceError(f"transport '{server.transport}' is not supported yet (stdio only)")
    if server.status != "active":
        raise MCPServiceError(f"MCP server '{server.name}' is disabled")

    client = MCPStdioClient(
        server.command_or_url,
        server.get_args(),
        env=server.get_env_secrets() or None,
        timeout=30.0,
    )
    try:
        with client:
            tools = client.list_tools()
            health = "healthy"
    except MCPClientError as exc:
        _record_health(db, server, "unreachable")
        _soft_disable_tools(db, server)
        raise MCPServiceError(f"MCP server '{server.name}' unreachable: {exc.message}") from exc

    remote_names = set()
    created, updated = [], []
    for tool in tools:
        qualified = f"mcp__{server.name}__{tool['name']}"
        remote_names.add(qualified)
        existing = db.query(ToolDefinition).filter(ToolDefinition.name == qualified).first()
        if existing:
            existing.description = tool["description"]
            existing.set_parameters(tool["input_schema"])
            updated.append(qualified)
            continue
        definition = ToolDefinition(
            id=str(uuid.uuid4()),
            name=qualified,
            display_name=f"{server.name}: {tool['name']}",
            description=tool["description"],
            category="mcp",
            risk_level="high",
            server_id=server.id,
            is_enabled=False,  # D7: enablement is a human decision
        )
        definition.set_parameters(tool["input_schema"])
        db.add(definition)
        created.append(qualified)

    # Remote tools that vanished: soft-disable, keep the row for history.
    local_mcp_tools = db.query(ToolDefinition).filter(ToolDefinition.server_id == server.id).all()
    vanished = [t.name for t in local_mcp_tools if t.name not in remote_names]
    for tool in local_mcp_tools:
        if tool.name not in remote_names:
            tool.is_enabled = False

    _record_health(db, server, "healthy")
    return {
        "server": server.name,
        "health": health,
        "tools_total": len(tools),
        "created": created,
        "updated": updated,
        "soft_disabled": vanished,
    }


def check_health(db: Session, server_id: str) -> Dict[str, Any]:
    """Probe the server (initialize + tools/list). Unreachable → its tools
    are soft-disabled (D8) so a dead server cannot strand the runtime."""
    server = get_server(db, server_id)
    try:
        client = MCPStdioClient(
            server.command_or_url,
            server.get_args(),
            env=server.get_env_secrets() or None,
            timeout=15.0,
        )
        with client:
            client.list_tools()
        _record_health(db, server, "healthy")
        return {"server": server.name, "health": "healthy"}
    except MCPClientError as exc:
        _record_health(db, server, "unreachable")
        _soft_disable_tools(db, server)
        return {"server": server.name, "health": "unreachable", "error": exc.message}


def _record_health(db: Session, server: MCPToolServer, health: str) -> None:
    server.last_health = health
    server.last_health_at = datetime.now(timezone.utc)
    db.commit()


def _soft_disable_tools(db: Session, server: MCPToolServer) -> None:
    for tool in db.query(ToolDefinition).filter(ToolDefinition.server_id == server.id).all():
        tool.is_enabled = False
    db.commit()


def call_tool(db: Session, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Direct MCP tool invocation (debugger path). Gates: server active +
    the qualified ToolDefinition exists and is human-enabled. The runtime
    loop additionally enforces the Station allowlist on its own path."""
    server = get_server(db, server_id)
    if server.status != "active":
        raise MCPServiceError(f"MCP server '{server.name}' is disabled")
    qualified = f"mcp__{server.name}__{tool_name}"
    definition = db.query(ToolDefinition).filter(
        ToolDefinition.name == qualified, ToolDefinition.server_id == server.id,
    ).first()
    if not definition:
        raise MCPServiceError(f"tool '{tool_name}' is not registered for server '{server.name}' — run sync first")
    if not definition.is_enabled:
        raise MCPServiceError(f"tool '{qualified}' is disabled — enable it in Model Manager first")
    client = MCPStdioClient(
        server.command_or_url,
        server.get_args(),
        env=server.get_env_secrets() or None,
        timeout=30.0,
    )
    try:
        with client:
            result = client.call_tool(tool_name, arguments)
    except MCPClientError as exc:
        _record_health(db, server, "unreachable")
        raise MCPServiceError(f"MCP server '{server.name}' unreachable: {exc.message}") from exc
    _record_health(db, server, "healthy")
    return result
