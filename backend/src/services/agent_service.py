from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.models.agent import AgentStation
from src.schemas.agent import AgentCreate, AgentUpdate
from src.data.agent_templates import get_template


class AgentServiceError(Exception):
    pass


class AgentNotFoundError(AgentServiceError):
    pass


class AgentValidationError(AgentServiceError):
    pass


def _merge_with_template(data: AgentCreate) -> dict:
    merged = data.model_dump(exclude_unset=True)
    template_id = merged.pop("template_id", None)
    if template_id:
        template = get_template(template_id)
        if not template:
            raise AgentValidationError(f"Template '{template_id}' not found")
        default_config = template["default_config"].copy()
        default_config["role"] = template["role"]
        default_config.update({k: v for k, v in merged.items() if v is not None})
        merged = default_config
    return merged


def create_agent(db: Session, data: AgentCreate) -> AgentStation:
    merged = _merge_with_template(data)

    VALID_ROLES = {"planner", "coder", "reviewer", "research", "summarizer", "supervisor"}

    if not merged.get("name"):
        raise AgentValidationError("Agent name is required")
    if not merged.get("role"):
        raise AgentValidationError("Agent role is required")
    if merged.get("role") not in VALID_ROLES:
        raise AgentValidationError(f"Agent role must be one of: {', '.join(sorted(VALID_ROLES))}")
    if not merged.get("default_model_id"):
        raise AgentValidationError("Default model is required")

    agent = AgentStation(
        name=merged["name"],
        role=merged["role"],
        description=merged.get("description") or "",
        status="idle",
        default_model_id=merged["default_model_id"],
        system_prompt=merged.get("system_prompt") or "",
        output_format=merged.get("output_format") or "markdown",
        max_steps_per_task=merged.get("max_steps_per_task", 10),
        allow_handoff=merged.get("allow_handoff", False),
        handoff_threshold_tokens=merged.get("handoff_threshold_tokens"),
        is_enabled=True,
        total_tasks_completed=0,
        total_tasks_failed=0,
        total_handoffs_initiated=0,
    )
    agent.set_backup_model_ids(merged.get("backup_model_ids") or [])
    agent.set_allowed_tools(merged.get("allowed_tools") or [])

    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def get_agent(db: Session, agent_id: str) -> AgentStation:
    agent = db.query(AgentStation).filter(AgentStation.id == agent_id).first()
    if not agent:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found")
    return agent


def list_agents(
    db: Session,
    role: Optional[str] = None,
    status: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[AgentStation], int]:
    query = db.query(AgentStation)

    if role:
        query = query.filter(AgentStation.role == role)
    if status:
        query = query.filter(AgentStation.status == status)
    if is_enabled is not None:
        query = query.filter(AgentStation.is_enabled == is_enabled)
    if search:
        query = query.filter(
            or_(
                AgentStation.name.ilike(f"%{search}%"),
                AgentStation.description.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    agents = query.order_by(AgentStation.role, AgentStation.name).offset((page - 1) * page_size).limit(page_size).all()
    return agents, total


def update_agent(db: Session, agent_id: str, data: AgentUpdate) -> AgentStation:
    agent = get_agent(db, agent_id)
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "backup_model_ids" and value is not None:
            agent.set_backup_model_ids(value)
        elif field == "allowed_tools" and value is not None:
            agent.set_allowed_tools(value)
        elif hasattr(agent, field):
            setattr(agent, field, value)

    db.commit()
    db.refresh(agent)
    return agent


def update_agent_status(db: Session, agent_id: str, is_enabled: bool) -> AgentStation:
    agent = get_agent(db, agent_id)
    agent.is_enabled = is_enabled
    db.commit()
    db.refresh(agent)
    return agent


def delete_agent(db: Session, agent_id: str) -> None:
    agent = get_agent(db, agent_id)
    db.delete(agent)
    db.commit()
