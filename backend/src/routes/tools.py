from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.tool import ToolCallRecord, ToolDefinition
from src.schemas.tool import (
    ToolCallListResponse,
    ToolCallRecordOut,
    ToolCreate,
    ToolListResponse,
    ToolOut,
    ToolUpdate,
)

router = APIRouter(tags=["tools"])


def _success_response(data):
    return {"success": True, "data": data}


def _error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.get("/tools")
def list_tools(
    category: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(ToolDefinition)

    if category:
        query = query.filter(ToolDefinition.category == category)
    if risk_level:
        query = query.filter(ToolDefinition.risk_level == risk_level)
    if is_enabled is not None:
        query = query.filter(ToolDefinition.is_enabled == is_enabled)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    tools = query.offset((page - 1) * page_size).limit(page_size).all()

    items = [ToolOut(**t.to_dict()).model_dump() for t in tools]
    return _success_response(
        ToolListResponse(
            items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
        ).model_dump()
    )


@router.get("/tools/calls")
def list_tool_calls(
    goal_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    tool_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(ToolCallRecord)

    if goal_id:
        query = query.filter(ToolCallRecord.goal_id == goal_id)
    if task_id:
        query = query.filter(ToolCallRecord.task_id == task_id)
    if agent_id:
        query = query.filter(ToolCallRecord.agent_id == agent_id)
    if tool_name:
        query = query.filter(ToolCallRecord.tool_name == tool_name)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    calls = query.order_by(ToolCallRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [ToolCallRecordOut(**c.to_dict()).model_dump() for c in calls]
    return _success_response(
        ToolCallListResponse(
            items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
        ).model_dump()
    )


@router.get("/tools/calls/{call_id}")
def get_tool_call(call_id: str, db: Session = Depends(get_db)):
    call = db.query(ToolCallRecord).filter(ToolCallRecord.id == call_id).first()
    if not call:
        _error_response("NOT_FOUND", f"Tool call '{call_id}' not found", 404)
    return _success_response(ToolCallRecordOut(**call.to_dict()).model_dump())


@router.get("/tools/{tool_id}")
def get_tool(tool_id: str, db: Session = Depends(get_db)):
    tool = db.query(ToolDefinition).filter(ToolDefinition.id == tool_id).first()
    if not tool:
        _error_response("NOT_FOUND", f"Tool '{tool_id}' not found", 404)
    return _success_response(ToolOut(**tool.to_dict()).model_dump())


@router.post("/tools", status_code=201)
def create_tool(data: ToolCreate, db: Session = Depends(get_db)):
    existing = db.query(ToolDefinition).filter(ToolDefinition.name == data.name).first()
    if existing:
        _error_response("CONFLICT", f"Tool with name '{data.name}' already exists", 409)

    tool = ToolDefinition(
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        category=data.category,
        risk_level=data.risk_level,
        is_enabled=data.is_enabled if data.is_enabled is not None else True,
    )
    tool.set_parameters(data.parameters)

    db.add(tool)
    db.commit()
    db.refresh(tool)
    return _success_response(ToolOut(**tool.to_dict()).model_dump())


@router.put("/tools/{tool_id}")
def update_tool(tool_id: str, data: ToolUpdate, db: Session = Depends(get_db)):
    tool = db.query(ToolDefinition).filter(ToolDefinition.id == tool_id).first()
    if not tool:
        _error_response("NOT_FOUND", f"Tool '{tool_id}' not found", 404)

    update_fields = {
        "display_name": data.display_name,
        "description": data.description,
        "category": data.category,
        "risk_level": data.risk_level,
        "is_enabled": data.is_enabled,
    }
    for field, value in update_fields.items():
        if value is not None:
            setattr(tool, field, value)

    if data.parameters is not None:
        tool.set_parameters(data.parameters)

    db.commit()
    db.refresh(tool)
    return _success_response(ToolOut(**tool.to_dict()).model_dump())


@router.delete("/tools/{tool_id}")
def delete_tool(tool_id: str, db: Session = Depends(get_db)):
    tool = db.query(ToolDefinition).filter(ToolDefinition.id == tool_id).first()
    if not tool:
        _error_response("NOT_FOUND", f"Tool '{tool_id}' not found", 404)

    db.delete(tool)
    db.commit()
    return _success_response({"id": tool_id, "deleted": True})


@router.patch("/tools/{tool_id}/toggle")
def toggle_tool(tool_id: str, db: Session = Depends(get_db)):
    tool = db.query(ToolDefinition).filter(ToolDefinition.id == tool_id).first()
    if not tool:
        _error_response("NOT_FOUND", f"Tool '{tool_id}' not found", 404)

    tool.is_enabled = not tool.is_enabled
    db.commit()
    db.refresh(tool)
    return _success_response({"id": tool.id, "is_enabled": tool.is_enabled})
