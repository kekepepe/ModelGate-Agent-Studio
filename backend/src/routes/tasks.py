from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
