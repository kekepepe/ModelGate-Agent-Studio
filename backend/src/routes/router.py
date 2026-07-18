from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.router import (
    RoutingRequest,
    RoutingResult,
    OverrideRequest,
    OverrideResponse,
    RoutingRulesResponse,
    ScoreBreakdown,
    DimensionScore,
    RoutingReason,
    RiskFlag,
    AgentSelectionRequest,
)
from src.services import agent_selector_service, capability_registry_service, router_service

router = APIRouter(tags=["router"])


def _success_response(data):
    return {"success": True, "data": data}


def _error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


def _build_routing_result_response(result: dict) -> dict:
    """Convert service result dict to API response dict matching RoutingResult schema."""
    score_breakdown = []
    for sb in result.get("score_breakdown", []):
        dimension_scores = []
        for ds in sb.get("dimension_scores", []):
            dimension_scores.append({
                "dimension": ds["dimension"],
                "score": ds["score"],
                "weight": ds["weight"],
                "weighted_score": ds["weighted_score"],
                "reason": ds["reason"],
            })
        score_breakdown.append({
            "model_id": sb["model_id"],
            "model_name": sb["model_name"],
            "total_score": sb["total_score"],
            "dimension_scores": dimension_scores,
        })

    risk_flags = []
    for rf in result.get("risk_flags", []):
        risk_flags.append({
            "type": rf["type"],
            "severity": rf["severity"],
            "message": rf["message"],
            "suggestion": rf.get("suggestion"),
        })

    routing_reason = result.get("routing_reason", {})

    return {
        "selected_model_id": result["selected_model_id"],
        "selected_agent_id": result.get("selected_agent_id"),
        "backup_model_ids": result.get("backup_model_ids", []),
        "routing_reason": {
            "summary": routing_reason.get("summary", ""),
            "primary_factors": routing_reason.get("primary_factors", []),
            "secondary_factors": routing_reason.get("secondary_factors", []),
            "tradeoffs": routing_reason.get("tradeoffs", []),
        },
        "confidence": result["confidence"],
        "risk_flags": risk_flags,
        "score_breakdown": score_breakdown,
        "is_user_override": result.get("is_user_override", False),
        "override_note": result.get("override_note"),
    }


@router.post("/router/select-model")
def select_model(data: RoutingRequest, db: Session = Depends(get_db)):
    try:
        result = router_service.select_model(
            db=db,
            task_id=data.task_id,
            task_type=data.task_type,
            task_complexity=data.task_complexity,
            task_description=data.task_description,
            required_capabilities=data.required_capabilities,
            preferred_agent_id=data.preferred_agent_id,
            preferred_model_id=data.preferred_model_id,
            context_length_estimate=data.context_length_estimate,
            has_vision_input=data.has_vision_input,
            requires_tool_calling=data.requires_tool_calling,
            budget_preference=data.budget_preference,
            speed_preference=data.speed_preference,
        )
        return _success_response(_build_routing_result_response(result))
    except router_service.NoEligibleModelError as e:
        _error_response("NO_ELIGIBLE_MODEL", str(e), 503)
    except router_service.InvalidOverrideError as e:
        _error_response("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.post("/router/override-model")
def override_model(data: OverrideRequest, db: Session = Depends(get_db)):
    try:
        result = router_service.override_model(
            db=db,
            task_id=data.task_id,
            selected_model_id=data.selected_model_id,
            original_model_id=data.original_model_id,
            reason=data.reason,
        )
        return _success_response({
            "task_id": result["task_id"],
            "selected_model_id": result["selected_model_id"],
            "is_user_override": result["is_user_override"],
            "override_note": result["override_note"],
        })
    except router_service.InvalidOverrideError as e:
        _error_response("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error_response("INTERNAL_ERROR", str(e), 500)


@router.get("/router/rules")
def get_routing_rules():
    rules = router_service.get_routing_rules()
    return _success_response({
        "weights": rules["weights"],
        "role_preferences": rules["role_preferences"],
        "hard_constraints": rules["hard_constraints"],
    })


@router.get("/capabilities")
def get_capability_registry(db: Session = Depends(get_db)):
    return _success_response({
        "available_capabilities": capability_registry_service.CAPABILITIES,
        "agents": capability_registry_service.list_registry(db),
    })


@router.post("/router/select-agent")
def select_agent(data: AgentSelectionRequest, db: Session = Depends(get_db)):
    try:
        result = agent_selector_service.select_agent(db, **data.model_dump())
        db.commit()
        return _success_response(result)
    except agent_selector_service.NoEligibleAgentError as exc:
        db.rollback()
        _error_response("NO_ELIGIBLE_AGENT", str(exc), 503)


@router.get("/goals/{goal_id}/selection-decisions")
def get_selection_decisions(goal_id: str, db: Session = Depends(get_db)):
    return _success_response(agent_selector_service.list_decisions(db, goal_id))
