from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.planning import ReplanRequest
from src.schemas.workspace import GoalCreate
from src.services import goal_service, planning_service, replan_service

router = APIRouter(tags=["goals"])


def _success(data, status_code=200):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.post("/goals", status_code=201)
def create_goal(data: GoalCreate, db: Session = Depends(get_db)):
    try:
        goal = goal_service.create_goal(
            db, data.title, data.description, data.execution_mode, data.workspace_root,
            data.budget_tokens, data.budget_cost_usd, data.max_duration_seconds,
            data.team_preset, data.max_parallel_tasks,
        )
        return _success({"goal_id": goal.id, "status": goal.status}, 201)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


@router.post("/goals/{goal_id}/start")
def start_goal(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = goal_service.start_goal(db, goal_id)
        return _success(result)
    except goal_service.GoalNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except goal_service.GoalValidationError as e:
        _error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


@router.get("/goals/{goal_id}/plans")
def list_goal_plans(goal_id: str, db: Session = Depends(get_db)):
    try:
        goal_service.get_goal(db, goal_id)
        return _success(planning_service.list_plans(db, goal_id))
    except goal_service.GoalNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)


@router.get("/goals/{goal_id}/plans/{version}")
def get_goal_plan(goal_id: str, version: int, db: Session = Depends(get_db)):
    try:
        goal_service.get_goal(db, goal_id)
        return _success(planning_service.get_plan(db, goal_id, version))
    except (goal_service.GoalNotFoundError, planning_service.PlanNotFoundError) as exc:
        _error("NOT_FOUND", str(exc), 404)


@router.post("/goals/{goal_id}/plans/{version}/confirm")
def confirm_goal_plan(goal_id: str, version: int, db: Session = Depends(get_db)):
    try:
        goal_service.get_goal(db, goal_id)
        return _success(planning_service.confirm_plan(db, goal_id, version))
    except (goal_service.GoalNotFoundError, planning_service.PlanNotFoundError) as exc:
        _error("NOT_FOUND", str(exc), 404)
    except planning_service.PlanValidationError as exc:
        _error("BAD_REQUEST", str(exc), 400)


@router.post("/goals/{goal_id}/replan")
def replan_goal(goal_id: str, data: ReplanRequest, db: Session = Depends(get_db)):
    try:
        return _success(replan_service.request_replan(db, goal_id, data))
    except goal_service.GoalNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)
    except replan_service.ReplanConflictError as exc:
        _error("CONFLICT", str(exc), 409)
    except replan_service.ReplanError as exc:
        _error("BAD_REQUEST", str(exc), 400)
