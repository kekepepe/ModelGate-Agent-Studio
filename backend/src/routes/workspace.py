from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/runs")
def list_runs(
    status: Optional[str] = Query(None), team_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None), page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db),
):
    return _success(workspace_service.list_runs(db, status, team_id, search, page, page_size))


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    try:
        return _success(workspace_service.get_run(db, run_id))
    except workspace_service.WorkspaceNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)


@router.get("/runs/{run_id}/workspace")
def get_run_workspace(run_id: str, db: Session = Depends(get_db)):
    try:
        return _success(workspace_service.get_run_workspace_state(db, run_id))
    except workspace_service.WorkspaceNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)


@router.get("/runs/{run_id}/assets")
def get_run_assets(run_id: str, db: Session = Depends(get_db)):
    try:
        return _success(workspace_service.list_run_assets(db, run_id))
    except workspace_service.WorkspaceNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)


@router.post("/runs/{run_id}/export")
def export_run(run_id: str, db: Session = Depends(get_db)):
    try:
        return _success(workspace_service.export_run_snapshot(db, run_id))
    except workspace_service.WorkspaceNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)
