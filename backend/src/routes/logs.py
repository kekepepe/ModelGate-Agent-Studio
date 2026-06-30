from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.log import ExecutionLogCreate
from src.services import log_service

router = APIRouter(tags=["logs"])


def _success_response(data):
    return {"success": True, "data": data}


def _error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.post("/logs", status_code=201)
def create_log(data: ExecutionLogCreate, db: Session = Depends(get_db)):
    try:
        log = log_service.create_log(db, data.model_dump(exclude_unset=True))
        return _success_response({"log_id": log.id})
    except log_service.LogValidationError as e:
        _error_response("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/logs")
def list_logs(
    goal_id: Optional[str] = Query(None),
    task_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    handoff_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    event_status: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    try:
        result = log_service.list_logs(
            db=db,
            goal_id=goal_id,
            task_id=task_id,
            agent_id=agent_id,
            model_id=model_id,
            handoff_id=handoff_id,
            event_type=event_type,
            event_status=event_status,
            start_time=start_time,
            end_time=end_time,
            search=search,
            page=page,
            page_size=page_size,
        )
        return _success_response(result)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/logs/{log_id}")
def get_log(log_id: str, db: Session = Depends(get_db)):
    try:
        return _success_response(log_service.get_log(db, log_id))
    except log_service.LogNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/logs/task/{task_id}/timeline")
def get_task_timeline(task_id: str, db: Session = Depends(get_db)):
    try:
        return _success_response(log_service.get_task_timeline(db, task_id))
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)
