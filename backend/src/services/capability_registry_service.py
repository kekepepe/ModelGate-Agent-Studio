"""Agent capability registry with backward-compatible role defaults."""

from typing import Dict, List

from sqlalchemy.orm import Session

from src.models.agent import AgentStation


CAPABILITIES = [
    "planning", "research", "code_read", "code_edit", "test", "review",
    "security_review", "document_write", "data_analysis", "tool_orchestration",
    "supervision", "direct",
]

ROLE_DEFAULTS: Dict[str, Dict[str, float]] = {
    "planner": {"planning": 1.0, "tool_orchestration": 0.9, "direct": 0.6},
    "research": {"research": 1.0, "data_analysis": 0.8, "document_write": 0.6},
    "coder": {"code_read": 1.0, "code_edit": 1.0, "test": 0.9},
    "reviewer": {"review": 1.0, "security_review": 0.85, "code_read": 0.8},
    "summarizer": {"direct": 1.0, "document_write": 1.0},
    "supervisor": {"supervision": 1.0, "review": 0.85, "planning": 0.7},
}

ROLE_DEFAULT_TOOLS: Dict[str, List[str]] = {
    "planner": ["workspace_list", "file_read"],
    "research": ["workspace_list", "file_read", "web_search"],
    "coder": [
        "workspace_list", "file_read", "file_search", "glob_search", "directory_create",
        "file_create", "file_write", "file_patch", "checkpoint_create", "checkpoint_restore",
        "terminal_execute", "test_runner", "lint_run", "typecheck_run", "build_run",
        "git_status", "git_log", "git_diff", "artifact_register",
    ],
    "reviewer": ["file_read", "diff_view", "git_diff", "terminal_execute", "test_runner"],
    "summarizer": ["file_read"],
    "supervisor": ["file_read"],
}


def default_capability_profile(role: str) -> Dict[str, float]:
    return dict(ROLE_DEFAULTS.get(role, {}))


def capability_profile(agent: AgentStation) -> Dict[str, float]:
    return agent.get_capability_profile() or default_capability_profile(agent.role)


def allowed_tools(agent: AgentStation) -> List[str]:
    configured = agent.get_allowed_tools()
    if configured or agent.get_capability_profile():
        return configured
    return list(ROLE_DEFAULT_TOOLS.get(agent.role, []))


def list_registry(db: Session) -> List[dict]:
    agents = db.query(AgentStation).order_by(AgentStation.name.asc()).all()
    return [{
        "agent_id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "enabled": agent.is_enabled,
        "capabilities": capability_profile(agent),
        "models": [agent.default_model_id, *agent.get_backup_model_ids()],
        "tools": allowed_tools(agent),
        "workspace_permissions": agent.get_workspace_permissions(),
        "input_types": agent.get_input_types(),
        "output_types": agent.get_output_types(),
        "limits": {
            "max_concurrency": agent.max_concurrency,
            "max_tokens": agent.max_tokens_per_task,
            "max_steps": agent.max_steps_per_task,
            "max_failures": agent.max_consecutive_failures,
        },
        "history": {
            "completed": agent.total_tasks_completed,
            "failed": agent.total_tasks_failed,
            "average_tokens": agent.average_tokens_per_task,
            "average_duration_ms": agent.average_duration_ms,
            "average_cost_usd": agent.average_cost_usd,
        },
    } for agent in agents]
