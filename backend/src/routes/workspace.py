from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services import workspace_service

router = APIRouter(tags=["workspace"])


def _success(data):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.get("/workspace/{goal_id}/state")
def get_workspace_state(goal_id: str, db: Session = Depends(get_db)):
    try:
        return _success(workspace_service.get_workspace_state(db, goal_id))
    except workspace_service.WorkspaceNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)
