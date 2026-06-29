from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.quota import (
    RecordUsageRequest,
    RecordUsageResponse,
    UpdateQuotaRequest,
    UpdateStatusRequest,
    QuotaOverviewResponse,
    QuotaStatusResponse,
    QuotaRecordResponse,
)
from src.services import quota_service

router = APIRouter(tags=["quota"])


def _success_response(data):
    return {"success": True, "data": data}


def _error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.post("/quota/record-usage")
def record_usage(data: RecordUsageRequest, db: Session = Depends(get_db)):
    try:
        result = quota_service.record_usage(
            db=db,
            provider=data.provider,
            model_id=data.model_id,
            model_name=data.model_name,
            request_tokens=data.request_tokens,
            response_tokens=data.response_tokens,
            total_tokens=data.total_tokens,
            error_code=data.error_code,
            error_type=data.error_type,
        )
        return _success_response(result)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/quota/overview")
def get_overview(
    provider: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "usage_percent",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    try:
        result = quota_service.get_overview(
            db=db,
            provider=provider,
            quota_status=status,
            sort_by=sort_by,
            order=order,
        )
        return _success_response(result)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/quota/models/{model_id}/status")
def get_model_status(model_id: str, db: Session = Depends(get_db)):
    try:
        result = quota_service.get_model_status(db=db, model_id=model_id)
        return _success_response(result)
    except quota_service.QuotaNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.patch("/quota/models/{model_id}/quota")
def update_quota_config(model_id: str, data: UpdateQuotaRequest, db: Session = Depends(get_db)):
    try:
        result = quota_service.update_quota_config(
            db=db,
            model_id=model_id,
            token_limit=data.token_limit,
            request_limit=data.request_limit,
            cost_limit=data.cost_limit,
            reset_period=data.reset_period,
            reset_date=data.reset_date,
        )
        return _success_response(result)
    except quota_service.QuotaNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except quota_service.InvalidQuotaConfigError as e:
        _error_response("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.patch("/quota/models/{model_id}/status")
def update_quota_status(model_id: str, data: UpdateStatusRequest, db: Session = Depends(get_db)):
    try:
        result = quota_service.update_quota_status(
            db=db,
            model_id=model_id,
            quota_status=data.quota_status,
            reason=data.reason,
            cooldown_until=data.cooldown_until,
        )
        return _success_response(result)
    except quota_service.QuotaNotFoundError as e:
        _error_response("NOT_FOUND", str(e), 404)
    except quota_service.InvalidQuotaConfigError as e:
        _error_response("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/quota/models/{model_id}/intercept")
def check_intercept(model_id: str, db: Session = Depends(get_db)):
    try:
        result = quota_service.check_and_intercept(db=db, model_id=model_id)
        if result and result.get("intercepted"):
            return _success_response(result)
        return _success_response({"intercepted": False})
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)
