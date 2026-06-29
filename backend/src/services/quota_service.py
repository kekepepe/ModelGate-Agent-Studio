from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from src.models.quota import QuotaRecord
from src.data.quota_thresholds import (
    DEFAULT_THRESHOLDS,
    QUOTA_STATUS_NORMAL,
    QUOTA_STATUS_WARNING,
    QUOTA_STATUS_NEAR_LIMIT,
    QUOTA_STATUS_LIMITED,
    QUOTA_STATUS_COOLDOWN,
    QUOTA_STATUS_UNKNOWN,
    QUOTA_MODE_KNOWN,
    QUOTA_MODE_ESTIMATED,
    QUOTA_MODE_UNKNOWN,
    LIMIT_ERROR_CODES,
    RATE_LIMIT_ERROR_CODES,
)


class QuotaServiceError(Exception):
    pass


class QuotaNotFoundError(QuotaServiceError):
    pass


class InvalidQuotaConfigError(QuotaServiceError):
    pass


def _calculate_usage_percent(record: QuotaRecord) -> Optional[float]:
    """Calculate usage_percent based on quota_mode."""
    if record.quota_mode == QUOTA_MODE_KNOWN and record.token_limit and record.token_limit > 0:
        return round(record.total_tokens / record.token_limit, 4)
    # estimated mode: MVP simplified, treat as unknown
    return None


def _calculate_estimated_remaining(record: QuotaRecord) -> Optional[int]:
    """Calculate estimated_remaining tokens."""
    if record.quota_mode == QUOTA_MODE_KNOWN and record.token_limit and record.token_limit > 0:
        return max(record.token_limit - record.total_tokens, 0)
    return None


def _determine_quota_status(record: QuotaRecord) -> str:
    """Determine quota_status based on usage_percent, error counts, and cooldown."""
    # Check cooldown first
    if record.cooldown_until and record.cooldown_until > datetime.now(timezone.utc):
        return QUOTA_STATUS_COOLDOWN

    # Check limit errors
    if record.limit_error_count > 0:
        return QUOTA_STATUS_LIMITED

    usage_percent = _calculate_usage_percent(record)
    if usage_percent is None:
        # No limit set
        if record.request_count > 0:
            return QUOTA_STATUS_NORMAL
        return QUOTA_STATUS_UNKNOWN

    # Check thresholds
    near_limit = DEFAULT_THRESHOLDS["near_limit_percent"]
    warning = DEFAULT_THRESHOLDS["warning_percent"]

    if usage_percent >= 1.0:
        return QUOTA_STATUS_LIMITED
    elif usage_percent >= near_limit:
        return QUOTA_STATUS_NEAR_LIMIT
    elif usage_percent >= warning:
        return QUOTA_STATUS_WARNING
    else:
        return QUOTA_STATUS_NORMAL


def _build_risk_flags(record: QuotaRecord) -> List[str]:
    """Build risk flags based on quota status."""
    flags = []
    if record.quota_status == QUOTA_STATUS_NEAR_LIMIT:
        flags.append("near_quota_limit")
    elif record.quota_status == QUOTA_STATUS_LIMITED:
        flags.append("quota_exhausted")
    elif record.quota_status == QUOTA_STATUS_COOLDOWN:
        flags.append("rate_limited")
    elif record.quota_status == QUOTA_STATUS_UNKNOWN:
        flags.append("quota_unknown")
    return flags


def _is_limit_error(error_code: Optional[int], error_type: Optional[str]) -> bool:
    """Check if error code is a limit-related error."""
    if error_code and error_code in LIMIT_ERROR_CODES:
        return True
    if error_type and error_type.lower() in {"insufficient_quota", "payment_required", "quota_exceeded"}:
        return True
    return False


def _is_rate_limit_error(error_code: Optional[int], error_type: Optional[str]) -> bool:
    """Check if error code is a rate limit error."""
    if error_code and error_code in RATE_LIMIT_ERROR_CODES:
        return True
    if error_type and error_type.lower() in {"rate_limit_exceeded", "overloaded"}:
        return True
    return False


def record_usage(
    db: Session,
    provider: str,
    model_id: str,
    model_name: Optional[str] = None,
    request_tokens: int = 0,
    response_tokens: int = 0,
    total_tokens: int = 0,
    error_code: Optional[int] = None,
    error_type: Optional[str] = None,
) -> Dict:
    """Record a model API call usage."""
    # Find or create QuotaRecord
    record = db.query(QuotaRecord).filter(
        QuotaRecord.provider == provider,
        QuotaRecord.model_id == model_id,
    ).first()

    if not record:
        record = QuotaRecord(
            provider=provider,
            model_id=model_id,
            model_name=model_name or model_id,
            request_count=0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            limit_error_count=0,
            handoff_triggered_count=0,
        )
        db.add(record)

    # Update model_name if provided
    if model_name:
        record.model_name = model_name

    # Always update last_used_at and request_count
    record.last_used_at = datetime.now(timezone.utc)
    record.request_count += 1

    # Handle limit errors
    is_limit_err = _is_limit_error(error_code, error_type)
    is_rate_limit = _is_rate_limit_error(error_code, error_type)

    if is_limit_err:
        record.limit_error_count += 1
        if is_rate_limit:
            # Set cooldown period
            cooldown_minutes = DEFAULT_THRESHOLDS["cooldown_minutes"]
            record.cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=cooldown_minutes)
    else:
        # Only accumulate tokens on successful calls
        if request_tokens > 0:
            record.input_tokens += request_tokens
        if response_tokens > 0:
            record.output_tokens += response_tokens
        if total_tokens > 0:
            record.total_tokens += total_tokens
        else:
            record.total_tokens = record.input_tokens + record.output_tokens

    # Recalculate derived fields
    record.usage_percent = _calculate_usage_percent(record)
    record.estimated_remaining = _calculate_estimated_remaining(record)
    record.quota_status = _determine_quota_status(record)
    record.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(record)

    return {
        "quota_record_id": record.id,
        "updated_status": record.quota_status,
        "usage_percent": record.usage_percent,
        "estimated_remaining": record.estimated_remaining,
        "risk_flags": _build_risk_flags(record),
    }


def get_overview(
    db: Session,
    provider: Optional[str] = None,
    quota_status: Optional[str] = None,
    sort_by: str = "usage_percent",
    order: str = "desc",
) -> Dict:
    """Get quota overview for all models."""
    query = db.query(QuotaRecord)

    if provider:
        query = query.filter(QuotaRecord.provider == provider)
    if quota_status:
        query = query.filter(QuotaRecord.quota_status == quota_status)

    # Sorting
    if sort_by == "usage_percent":
        # Handle NULLs: put unknown at the end
        from sqlalchemy import desc, asc, nulls_last
        if order == "desc":
            query = query.order_by(nulls_last(desc(QuotaRecord.usage_percent)))
        else:
            query = query.order_by(nulls_last(asc(QuotaRecord.usage_percent)))
    elif sort_by == "last_used_at":
        if order == "desc":
            query = query.order_by(QuotaRecord.last_used_at.desc())
        else:
            query = query.order_by(QuotaRecord.last_used_at.asc())
    elif sort_by == "request_count":
        if order == "desc":
            query = query.order_by(QuotaRecord.request_count.desc())
        else:
            query = query.order_by(QuotaRecord.request_count.asc())

    records = query.all()

    # Build summary counts
    counts = {
        QUOTA_STATUS_NORMAL: 0,
        QUOTA_STATUS_WARNING: 0,
        QUOTA_STATUS_NEAR_LIMIT: 0,
        QUOTA_STATUS_LIMITED: 0,
        QUOTA_STATUS_COOLDOWN: 0,
        QUOTA_STATUS_UNKNOWN: 0,
    }
    for r in records:
        counts[r.quota_status] = counts.get(r.quota_status, 0) + 1

    summary = {
        "total_models": len(records),
        "normal_count": counts[QUOTA_STATUS_NORMAL],
        "warning_count": counts[QUOTA_STATUS_WARNING],
        "near_limit_count": counts[QUOTA_STATUS_NEAR_LIMIT],
        "limited_count": counts[QUOTA_STATUS_LIMITED],
        "cooldown_count": counts[QUOTA_STATUS_COOLDOWN],
        "unknown_count": counts[QUOTA_STATUS_UNKNOWN],
    }

    models = []
    for r in records:
        models.append({
            "quota_record_id": r.id,
            "provider": r.provider,
            "model_id": r.model_id,
            "model_name": r.model_name,
            "request_count": r.request_count,
            "total_tokens": r.total_tokens,
            "quota_status": r.quota_status,
            "usage_percent": r.usage_percent,
            "estimated_remaining": r.estimated_remaining,
            "last_used_at": r.last_used_at.isoformat() if r.last_used_at else None,
            "limit_error_count": r.limit_error_count,
            "handoff_triggered_count": r.handoff_triggered_count,
        })

    return {
        "summary": summary,
        "models": models,
    }


def get_model_status(db: Session, model_id: str) -> Dict:
    """Get quota status for a single model."""
    record = db.query(QuotaRecord).filter(QuotaRecord.model_id == model_id).first()
    if not record:
        raise QuotaNotFoundError(f"Quota record for model {model_id} not found")

    return {
        "quota_record_id": record.id,
        "provider": record.provider,
        "model_id": record.model_id,
        "model_name": record.model_name,
        "request_count": record.request_count,
        "input_tokens": record.input_tokens,
        "output_tokens": record.output_tokens,
        "total_tokens": record.total_tokens,
        "last_used_at": record.last_used_at.isoformat() if record.last_used_at else None,
        "estimated_remaining": record.estimated_remaining,
        "quota_status": record.quota_status,
        "limit_error_count": record.limit_error_count,
        "cooldown_until": record.cooldown_until.isoformat() if record.cooldown_until else None,
        "handoff_triggered_count": record.handoff_triggered_count,
        "usage_percent": record.usage_percent,
        "quota_mode": record.quota_mode,
        "token_limit": record.token_limit,
    }


def update_quota_config(
    db: Session,
    model_id: str,
    token_limit: Optional[int] = None,
    request_limit: Optional[int] = None,
    cost_limit: Optional[float] = None,
    reset_period: Optional[str] = None,
    reset_date: Optional[int] = None,
) -> Dict:
    """Update quota configuration for a model."""
    record = db.query(QuotaRecord).filter(QuotaRecord.model_id == model_id).first()
    if not record:
        raise QuotaNotFoundError(f"Quota record for model {model_id} not found")

    if token_limit is not None:
        if token_limit <= 0:
            raise InvalidQuotaConfigError("token_limit must be greater than 0")
        record.token_limit = token_limit

    if request_limit is not None:
        if request_limit <= 0:
            raise InvalidQuotaConfigError("request_limit must be greater than 0")
        record.request_limit = request_limit

    if cost_limit is not None:
        record.cost_limit = cost_limit

    if reset_period is not None:
        record.reset_period = reset_period

    if reset_date is not None:
        record.reset_date = reset_date

    # Set mode to known if token_limit is set
    if record.token_limit and record.token_limit > 0:
        record.quota_mode = QUOTA_MODE_KNOWN
    elif record.request_limit and record.request_limit > 0:
        record.quota_mode = QUOTA_MODE_KNOWN

    # Recalculate derived fields
    record.usage_percent = _calculate_usage_percent(record)
    record.estimated_remaining = _calculate_estimated_remaining(record)
    record.quota_status = _determine_quota_status(record)
    record.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(record)

    return record.to_dict()


def update_quota_status(
    db: Session,
    model_id: str,
    quota_status: str,
    reason: Optional[str] = None,
    cooldown_until: Optional[str] = None,
) -> Dict:
    """Manually update quota status for a model."""
    record = db.query(QuotaRecord).filter(QuotaRecord.model_id == model_id).first()
    if not record:
        raise QuotaNotFoundError(f"Quota record for model {model_id} not found")

    # Prevent direct marking to LIMITED or COOLDOWN unless by system
    if quota_status in (QUOTA_STATUS_LIMITED, QUOTA_STATUS_COOLDOWN):
        raise InvalidQuotaConfigError(
            f"Cannot manually set status to {quota_status}. Use record_usage with error codes."
        )

    record.quota_status = quota_status

    if cooldown_until is not None:
        if cooldown_until:
            record.cooldown_until = datetime.fromisoformat(cooldown_until)
        else:
            record.cooldown_until = None

    record.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(record)

    return record.to_dict()


def check_and_intercept(db: Session, model_id: str) -> Optional[Dict]:
    """Check if model is LIMITED or COOLDOWN and return intercept info if so."""
    record = db.query(QuotaRecord).filter(QuotaRecord.model_id == model_id).first()
    if not record:
        return None  # No record means unknown, allow

    if record.quota_status in (QUOTA_STATUS_LIMITED, QUOTA_STATUS_COOLDOWN):
        return {
            "intercepted": True,
            "model_id": model_id,
            "quota_status": record.quota_status,
            "message": f"模型 {record.model_name} 额度已受限（{record.quota_status}），已触发自动 Handoff",
            "usage_percent": record.usage_percent,
            "estimated_remaining": record.estimated_remaining,
        }

    return {"intercepted": False}
