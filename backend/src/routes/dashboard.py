from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.dashboard import (
    DashboardAgentPerformanceResponse,
    DashboardStatsResponse,
    DashboardTrendsResponse,
)
from src.services import stats_service

router = APIRouter(tags=["dashboard"])


def _success_response(data):
    return {"success": True, "data": data}


def _error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    try:
        data = DashboardStatsResponse(**stats_service.get_dashboard_stats(db)).model_dump()
        return _success_response(data)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/dashboard/trends")
def get_dashboard_trends(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    try:
        data = DashboardTrendsResponse(**stats_service.get_dashboard_trends(db, days=days)).model_dump()
        return _success_response(data)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/dashboard/agent-performance")
def get_agent_performance(db: Session = Depends(get_db)):
    try:
        data = DashboardAgentPerformanceResponse(**stats_service.get_agent_performance(db)).model_dump()
        return _success_response(data)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)
