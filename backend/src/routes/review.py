from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services import review_service

router = APIRouter(tags=["review"])


def _success(data, status_code=200):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.post("/runtime/review/{goal_id}")
def generate_review(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = review_service.generate_review(db, goal_id)
        return _success(result)
    except review_service.ReviewError:
        raise _error("BAD_REQUEST", str(goal_id), 400)
    except Exception:
        raise _error("INTERNAL_ERROR", str(goal_id), 500)


@router.get("/runtime/review/{goal_id}")
def get_review(goal_id: str, db: Session = Depends(get_db)):
    result = review_service.get_review(db, goal_id)
    if result is None:
        raise _error("NOT_FOUND", f"No review found for goal '{goal_id}'", 404)
    return _success(result)
