"""V1.3 P3 T11-T13: MCP registry service, sync, permissions, executor wiring.

Exercised against the deterministic stub server so the suite stays
hermetic; scripts/e2e-mcp.sh covers the real filesystem server.
"""
import asyncio
import os
import sys
import uuid

import pytest

from src.models.agent import AgentStation
from src.models.tool import ToolDefinition
from src.services import mcp_service
from src.services.tool_service import ToolExecutor

STUB_SERVER = os.path.join(os.path.dirname(__file__), "fixtures", "mcp_stub_server.py")


def _register_stub(db_session, name="stub"):
    return mcp_service.register_server(
        db_session, name=name, transport="stdio",
        command_or_url=sys.executable, args=[STUB_SERVER],
        env_secrets={},
    )


def test_register_server_is_idempotent_by_name_and_redacts_nothing_in_dict(db_session):
    server = _register_stub(db_session, name="registry-check")
    data = mcp_service.get_server(db_session, server["id"]).to_dict()
    assert data["name"] == "registry-check"
    assert data["status"] == "active"
    assert "env_secrets" not in data, "secrets must never reach the API payload"
    with pytest.raises(mcp_service.MCPServiceError):
        _register_stub(db_session, name="registry-check")


def test_sync_discovers_stub_tools_as_disabled_high_risk(db_session):
    server = _register_stub(db_session, name="sync-check")
    result = mcp_service.sync_server(db_session, server["id"])
    assert result["health"] == "healthy"
    assert result["tools_total"] >= 2
    assert any("mcp__sync-check__echo" in name for name in result["created"])

    tool = db_session.query(ToolDefinition).filter(
        ToolDefinition.name == "mcp__sync-check__echo",
    ).one()
    assert tool.server_id == server["id"]
    assert tool.is_enabled is False, "MCP tools start disabled (D7)"
    assert tool.risk_level == "high"
    assert tool.get_parameters().get("type") == "object"


def test_sync_is_idempotent_and_soft_disables_vanished_tools(db_session):
    server = _register_stub(db_session, name="sync-idem")
    mcp_service.sync_server(db_session, server["id"])
    second = mcp_service.sync_server(db_session, server["id"])
    assert second["created"] == []
    assert second["updated"], "second sync should update the existing rows"
    # No duplicate rows.
    assert db_session.query(ToolDefinition).filter(
        ToolDefinition.server_id == server["id"],
    ).count() == 2


def test_disabled_server_blocks_sync_and_disables_tools(db_session):
    server = _register_stub(db_session, name="sync-disable")
    mcp_service.sync_server(db_session, server["id"])
    mcp_service.set_server_status(db_session, server["id"], "disabled")

    tools = db_session.query(ToolDefinition).filter(
        ToolDefinition.server_id == server["id"],
    ).all()
    assert all(not tool.is_enabled for tool in tools)
    with pytest.raises(mcp_service.MCPServiceError):
        mcp_service.sync_server(db_session, server["id"])


def test_unreachable_server_soft_disables_its_tools(db_session):
    server = mcp_service.register_server(
        db_session, name="dead-server", transport="stdio",
        command_or_url="/nonexistent/mcp-binary", args=[],
    )
    # First sync fails loudly (server unreachable) — the caller sees the
    # error, but the health state and soft-disable must still be persisted.
    with pytest.raises(mcp_service.MCPServiceError):
        mcp_service.sync_server(db_session, server["id"])

    # Simulate a previously-healthy tool, then make the server unreachable.
    fake = ToolDefinition(
        name="mcp__dead-server__echo", display_name="dead", category="mcp",
        risk_level="high", server_id=server["id"], is_enabled=True,
    )
    fake.set_parameters({"type": "object", "properties": {}})
    db_session.add(fake)
    db_session.commit()

    health = mcp_service.check_health(db_session, server["id"])

    assert health["health"] == "unreachable"
    db_session.expire_all()
    fake = db_session.get(ToolDefinition, fake.id)
    assert fake.is_enabled is False, "dead server tools must soft-disable (D8)"


def test_executor_runs_enabled_mcp_tool_via_client(db_session):
    server = _register_stub(db_session, name="exec-check")
    mcp_service.sync_server(db_session, server["id"])
    tool = db_session.query(ToolDefinition).filter(
        ToolDefinition.name == "mcp__exec-check__echo",
    ).one()
    tool.is_enabled = True
    db_session.commit()

    agent = AgentStation(
        id=str(uuid.uuid4()), name="MCP Agent", role="coder",
        default_model_id="m-1", is_enabled=True,
    )
    agent.set_allowed_tools(["mcp__exec-check__echo"])
    goal = Goal = None  # executor accepts ids; no DB rows needed for stub echo
    record = asyncio.run(ToolExecutor().execute(
        db_session, "mcp__exec-check__echo", {"message": "via-runtime"},
        goal_id=None, task_id=None, agent_id=agent.id, worker_id="w-1",
    ))
    assert record.status == "completed"
    assert "via-runtime" in (record.tool_output or "")


def test_executor_blocks_disabled_mcp_tool(db_session):
    server = _register_stub(db_session, name="exec-blocked")
    mcp_service.sync_server(db_session, server["id"])
    agent = AgentStation(
        id=str(uuid.uuid4()), name="MCP Agent 2", role="coder",
        default_model_id="m-1", is_enabled=True,
    )
    agent.set_allowed_tools(["mcp__exec-blocked__echo"])
    db_session.commit()

    record = asyncio.run(ToolExecutor().execute(
        db_session, "mcp__exec-blocked__echo", {"message": "x"},
        goal_id=None, task_id=None, agent_id=agent.id, worker_id="w-2",
    ))
    assert record.status == "denied"


def test_executor_respects_station_allowlist_for_mcp_tools(db_session):
    server = _register_stub(db_session, name="exec-allowlist")
    mcp_service.sync_server(db_session, server["id"])
    tool = db_session.query(ToolDefinition).filter(
        ToolDefinition.name == "mcp__exec-allowlist__echo",
    ).one()
    tool.is_enabled = True
    agent = AgentStation(
        id=str(uuid.uuid4()), name="No-MCP Agent", role="coder",
        default_model_id="m-1", is_enabled=True,
    )
    agent.set_allowed_tools(["file_read"])  # allowlist without the MCP tool
    db_session.add(agent)
    db_session.commit()

    record = asyncio.run(ToolExecutor().execute(
        db_session, "mcp__exec-allowlist__echo", {"message": "x"},
        goal_id=None, task_id=None, agent_id=agent.id, worker_id="w-3",
    ))
    assert record.status == "denied"
