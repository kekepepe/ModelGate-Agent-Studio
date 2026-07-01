from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.knowledge import ApprovalRequest
from src.services import curator_service

router = APIRouter(tags=["knowledge"])


def _success(data, status_code=200):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail={"success": False, "error": {"code": code, "message": message}})


@router.post("/knowledge/generate/{goal_id}")
def generate_memories(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = curator_service.generate_memories(db, goal_id)
        return _success(result)
    except Exception as e:
        raise _error("INTERNAL_ERROR", str(e), 500)


@router.get("/knowledge/evolution")
def get_evolution_summary(goal_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    try:
        return _success(curator_service.get_evolution_summary(db, goal_id))
    except Exception as e:
        raise _error("INTERNAL_ERROR", str(e), 500)


@router.post("/knowledge/memories/{memory_id}/approve")
def approve_memory(memory_id: str, req: ApprovalRequest, db: Session = Depends(get_db)):
    try:
        result = curator_service.approve_memory(db, memory_id, req.approved, req.approved_by)
        return _success(result)
    except ValueError as e:
        raise _error("NOT_FOUND", str(e), 404)
    except Exception as e:
        raise _error("INTERNAL_ERROR", str(e), 500)


@router.post("/knowledge/skills/{skill_id}/approve")
def approve_skill(skill_id: str, req: ApprovalRequest, db: Session = Depends(get_db)):
    try:
        result = curator_service.approve_skill(db, skill_id, req.approved, req.approved_by)
        return _success(result)
    except ValueError as e:
        raise _error("NOT_FOUND", str(e), 404)
    except Exception as e:
        raise _error("INTERNAL_ERROR", str(e), 500)
