from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.core.database import get_db
from src.services import task_service
from src.schemas.workspace import TaskCancelRequest, TaskSkipRequest, TaskSplitRequest

router = APIRouter(tags=["tasks"])


def _success(data):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.get("/tasks")
def list_tasks(
    agent_id: Optional[List[str]] = Query(None, description="Filter by one or more agent ids"),
    status: Optional[List[str]] = Query(None, description="Filter by one or more task statuses"),
    goal_id: Optional[str] = Query(None, description="Restrict to a single goal's tasks"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """V1.0-P1-2: filtered, paginated task list.

    Used by the frontend Sidebar to render a "current task" line per
    Station, and by any future per-agent task feed. Returns the same
    shape as `/api/v1/goals/{id}/state` task list, so the frontend
    can reuse the `WorkspaceTask` type.
    """
    try:
        return _success(
            task_service.list_tasks(
                db,
                agent_ids=agent_id,
                statuses=status,
                goal_id=goal_id,
                page=page,
                page_size=page_size,
            )
        )
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


@router.get("/tasks/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    try:
        return _success(task_service.get_task(db, task_id))
    except task_service.TaskNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, data: TaskCancelRequest, db: Session = Depends(get_db)):
    try:
        return _success(task_service.cancel_task(db, task_id, data.reason))
    except task_service.TaskNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)
    except task_service.TaskTransitionError as exc:
        _error("BAD_REQUEST", str(exc), 400)


@router.post("/tasks/{task_id}/retry")
def retry_task(task_id: str, db: Session = Depends(get_db)):
    try:
        return _success(task_service.retry_task(db, task_id))
    except task_service.TaskNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)
    except task_service.TaskTransitionError as exc:
        _error("BAD_REQUEST", str(exc), 400)


@router.post("/tasks/{task_id}/skip")
def skip_task(task_id: str, data: TaskSkipRequest, db: Session = Depends(get_db)):
    try:
        return _success(task_service.skip_task(db, task_id, data.reason))
    except task_service.TaskNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)
    except task_service.TaskTransitionError as exc:
        _error("BAD_REQUEST", str(exc), 400)


@router.post("/tasks/{task_id}/approve")
def approve_task(task_id: str, db: Session = Depends(get_db)):
    try:
        return _success(task_service.approve_task(db, task_id))
    except task_service.TaskNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)
    except task_service.TaskTransitionError as exc:
        _error("BAD_REQUEST", str(exc), 400)


@router.post("/tasks/{task_id}/split")
def split_task(task_id: str, data: TaskSplitRequest, db: Session = Depends(get_db)):
    try:
        return _success(task_service.split_task(db, task_id, data.titles))
    except task_service.TaskNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)
    except task_service.TaskTransitionError as exc:
        _error("BAD_REQUEST", str(exc), 400)
