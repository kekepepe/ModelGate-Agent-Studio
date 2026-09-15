"""MCP server registry + tool sync routes (V1.3 P3)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services import mcp_service

router = APIRouter(tags=["mcp"])


def _success(data, status_code=200):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail={"success": False, "error": {"code": code, "message": message}})


class MCPServerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    transport: str = Field("stdio", pattern="^(stdio|streamable_http)$")
    command_or_url: str = Field(..., min_length=1, max_length=2000)
    args: List[str] = Field(default_factory=list)
    env_secrets: dict = Field(default_factory=dict)


class MCPServerStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(active|disabled)$")


@router.post("/mcp/servers", status_code=201)
def register_server(req: MCPServerCreate, db: Session = Depends(get_db)):
    try:
        return _success(mcp_service.register_server(
            db, name=req.name, transport=req.transport,
            command_or_url=req.command_or_url, args=req.args,
            env_secrets=req.env_secrets,
        ), 201)
    except mcp_service.MCPServiceError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.get("/mcp/servers")
def list_servers(db: Session = Depends(get_db)):
    return _success(mcp_service.list_servers(db))


@router.post("/mcp/servers/{server_id}/sync")
def sync_server(server_id: str, db: Session = Depends(get_db)):
    try:
        return _success(mcp_service.sync_server(db, server_id))
    except mcp_service.MCPServerNotFoundError as exc:
        raise _error("NOT_FOUND", str(exc), 404)
    except mcp_service.MCPServiceError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.patch("/mcp/servers/{server_id}/status")
def update_server_status(server_id: str, req: MCPServerStatusRequest, db: Session = Depends(get_db)):
    try:
        return _success(mcp_service.set_server_status(db, server_id, req.status))
    except mcp_service.MCPServerNotFoundError as exc:
        raise _error("NOT_FOUND", str(exc), 404)
    except mcp_service.MCPServiceError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.get("/mcp/servers/{server_id}/health")
def check_server_health(server_id: str, db: Session = Depends(get_db)):
    try:
        return _success(mcp_service.check_health(db, server_id))
    except mcp_service.MCPServerNotFoundError as exc:
        raise _error("NOT_FOUND", str(exc), 404)


@router.post("/mcp/servers/{server_id}/call/{tool_name}")
def call_server_tool(server_id: str, tool_name: str, arguments: dict, db: Session = Depends(get_db)):
    """Direct MCP tool invocation — the MCP debugger path. Gates: server
    active + tool human-enabled (the Station allowlist applies on the
    runtime path separately)."""
    try:
        return _success(mcp_service.call_tool(db, server_id, tool_name, arguments))
    except mcp_service.MCPServerNotFoundError as exc:
        raise _error("NOT_FOUND", str(exc), 404)
    except mcp_service.MCPServiceError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)
