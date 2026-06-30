from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services import task_service

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
