from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.handoff import (
    HandoffAcceptRequest,
    HandoffResultRequest,
    HandoffTaskCreate,
    HandoffTriggerRequest,
)
from src.services import handoff_service

router = APIRouter(tags=["handoffs"])


def _success_response(data):
    return {"success": True, "data": data}


def _error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.post("/handoff/tasks", status_code=201)
def create_demo_task(data: HandoffTaskCreate, db: Session = Depends(get_db)):
    try:
        task = handoff_service.create_demo_task(db, data)
        return _success_response(task.to_dict())
    except handoff_service.HandoffNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except handoff_service.HandoffConflictError as e:
        _error_response("CONFLICT", str(e), 409)
    except handoff_service.HandoffValidationError as e:
        _error_response("BAD_REQUEST", str(e), 400)


@router.post("/tasks/{task_id}/handoff", status_code=201)
def trigger_handoff(task_id: str, data: HandoffTriggerRequest, db: Session = Depends(get_db)):
    try:
        result = handoff_service.trigger_handoff(
            db=db,
            task_id=task_id,
            to_agent_id=data.to_agent_id,
            to_model_id=data.to_model_id,
            reason=data.reason,
            reason_description=data.reason_description,
        )
        return _success_response(result)
    except handoff_service.HandoffNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except handoff_service.HandoffConflictError as e:
        _error_response("CONFLICT", str(e), 409)
    except handoff_service.HandoffValidationError as e:
        _error_response("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/handoffs")
def list_handoffs(
    goal_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    reason: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_agent_id: Optional[str] = Query(None),
    to_agent_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        result = handoff_service.list_handoffs(
            db=db,
            goal_id=goal_id,
            task_id=task_id,
            reason=reason,
            status=status,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            search=search,
            page=page,
            page_size=page_size,
        )
        return _success_response(result)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/handoffs/{handoff_id}")
def get_handoff(handoff_id: str, db: Session = Depends(get_db)):
    try:
        return _success_response(handoff_service.get_handoff(db, handoff_id))
    except handoff_service.HandoffNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.post("/handoffs/{handoff_id}/accept")
def accept_handoff(handoff_id: str, data: HandoffAcceptRequest, db: Session = Depends(get_db)):
    try:
        result = handoff_service.accept_handoff(
            db=db,
            handoff_id=handoff_id,
            agent_id=data.agent_id,
            model_id=data.model_id,
        )
        return _success_response(result)
    except handoff_service.HandoffNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except handoff_service.HandoffConflictError as e:
        _error_response("CONFLICT", str(e), 409)
    except handoff_service.HandoffValidationError as e:
        _error_response("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.patch("/handoffs/{handoff_id}/result")
def update_handoff_result(handoff_id: str, data: HandoffResultRequest, db: Session = Depends(get_db)):
    try:
        result = handoff_service.update_handoff_result(
            db=db,
            handoff_id=handoff_id,
            result_after_handoff=data.result_after_handoff,
            result_note=data.result_note,
        )
        return _success_response(result)
    except handoff_service.HandoffNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except handoff_service.HandoffValidationError as e:
        _error_response("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/logs")
def list_logs(handoff_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    try:
        return _success_response(handoff_service.list_logs(db, handoff_id=handoff_id))
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)
