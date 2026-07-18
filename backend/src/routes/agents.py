from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentStatusUpdate,
    AgentResponse,
    AgentListItem,
    AgentListResponse,
    AgentCreateResponse,
)
from src.services import agent_service
from src.data.agent_templates import list_templates

router = APIRouter(tags=["agents"])


def _success_response(data):
    return {"success": True, "data": data}


def _error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.get("/agents/templates")
def list_agent_templates():
    templates = list_templates()
    return _success_response(templates)


@router.get("/agents")
def list_agents(
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    agents, total = agent_service.list_agents(
        db, role=role, status=status, is_enabled=is_enabled, search=search, page=page, page_size=page_size
    )
    items = [
        AgentListItem(
            id=a.id,
            name=a.name,
            role=a.role,
            description=a.description,
            status=a.status,
            default_model_id=a.default_model_id,
            is_enabled=a.is_enabled,
            current_task_id=a.current_task_id,
            total_tasks_completed=a.total_tasks_completed,
            capabilities=sorted((a.get_capability_profile() or agent_service.default_capability_profile(a.role)).keys()),
            max_concurrency=a.max_concurrency,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in agents
    ]
    return _success_response(
        AgentListResponse(items=items, total=total, page=page, page_size=page_size).model_dump()
    )


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    try:
        agent = agent_service.get_agent(db, agent_id)
        return _success_response(AgentResponse(**agent.to_dict()).model_dump())
    except agent_service.AgentNotFoundError:
        _error_response("NOT_FOUND", f"Agent '{agent_id}' not found", 404)


@router.post("/agents", status_code=201)
def create_agent(data: AgentCreate, db: Session = Depends(get_db)):
    try:
        agent = agent_service.create_agent(db, data)
        return _success_response(
            AgentCreateResponse(
                id=agent.id,
                name=agent.name,
                role=agent.role,
                status=agent.status,
                created_at=agent.created_at.isoformat() if agent.created_at else None,
            ).model_dump()
        )
    except agent_service.AgentValidationError as e:
        _error_response("BAD_REQUEST", str(e), 400)


@router.patch("/agents/{agent_id}")
def update_agent(agent_id: str, data: AgentUpdate, db: Session = Depends(get_db)):
    try:
        agent = agent_service.update_agent(db, agent_id, data)
        return _success_response(AgentResponse(**agent.to_dict()).model_dump())
    except agent_service.AgentNotFoundError:
        _error_response("NOT_FOUND", f"Agent '{agent_id}' not found", 404)
    except agent_service.AgentValidationError as e:
        _error_response("BAD_REQUEST", str(e), 400)


@router.patch("/agents/{agent_id}/status")
def update_agent_status(agent_id: str, data: AgentStatusUpdate, db: Session = Depends(get_db)):
    try:
        agent = agent_service.update_agent_status(db, agent_id, data.is_enabled)
        return _success_response(
            {
                "id": agent.id,
                "is_enabled": agent.is_enabled,
                "status": agent.status,
            }
        )
    except agent_service.AgentNotFoundError:
        _error_response("NOT_FOUND", f"Agent '{agent_id}' not found", 404)
