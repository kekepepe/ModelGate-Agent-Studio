from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services import goal_service, runtime_service

router = APIRouter(tags=["runtime"])


def _success(data, status_code=200):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.post("/runtime/execute/{goal_id}")
def execute_goal(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = runtime_service.execute_goal_pipeline(db, goal_id)
        return _success(result)
    except goal_service.GoalNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except runtime_service.GoalNotReadyError as e:
        _error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


@router.post("/runtime/execute-step/{task_id}")
def execute_step(task_id: str, db: Session = Depends(get_db)):
    try:
        result = runtime_service.execute_task_step(db, task_id)
        return _success(result)
    except runtime_service.TaskNotReadyError as e:
        _error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


@router.get("/runtime/status/{goal_id}")
def get_runtime_status(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = runtime_service.get_runtime_status(db, goal_id)
        return _success(result)
    except goal_service.GoalNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)
