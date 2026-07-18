"""Capability-first joint Agent/model selection with auditable eliminations."""

import fnmatch
import json
import uuid
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.model import Model
from src.models.quota import QuotaRecord
from src.models.selection import AgentSelectionDecision
from src.models.workspace import Task
from src.services.capability_registry_service import allowed_tools, capability_profile


class NoEligibleAgentError(ValueError):
    pass


MODEL_CAPABILITIES = {
    "planning": {"planning", "reasoning"}, "research": {"long_context", "reasoning"},
    "code_read": {"code", "reasoning"}, "code_edit": {"code", "reasoning"},
    "test": {"code", "reasoning"}, "review": {"reasoning"},
    "security_review": {"reasoning"}, "document_write": {"summarization", "reasoning"},
    "data_analysis": {"reasoning"}, "tool_orchestration": {"tool_calling", "reasoning"},
    "supervision": {"planning", "reasoning"}, "direct": {"reasoning"},
}


def select_agent(
    db: Session, *, task_id: str, required_capabilities: List[str], required_tools: List[str],
    goal_id: Optional[str] = None, task_type: str = "general", risk_level: str = "low",
    workspace_scope: Optional[str] = None, input_type: str = "text", output_type: str = "text",
    context_length_estimate: int = 8000, require_model: bool = True, persist: bool = True,
    reserved_loads: Optional[Dict[str, int]] = None,
) -> Dict:
    agents = db.query(AgentStation).filter(AgentStation.is_enabled == True).order_by(AgentStation.created_at.asc()).all()
    models = {model.id: model for model in db.query(Model).filter(Model.is_enabled == True).all()}
    quotas = {item.model_id: item.quota_status for item in db.query(QuotaRecord).all()}
    active_loads = dict(
        db.query(Task.assigned_agent_id, func.count(Task.id))
        .filter(Task.status.in_(["assigned", "running"]), Task.assigned_agent_id.is_not(None))
        .group_by(Task.assigned_agent_id).all()
    )
    candidates = [
        _evaluate_candidate(
            agent, models=models, quotas=quotas,
            active_load=active_loads.get(agent.id, 0) + (reserved_loads or {}).get(agent.id, 0),
            required_capabilities=required_capabilities, required_tools=required_tools,
            risk_level=risk_level, workspace_scope=workspace_scope, input_type=input_type,
            output_type=output_type, context_length_estimate=context_length_estimate,
            require_model=require_model,
        )
        for agent in agents
    ]
    eligible = sorted(
        [candidate for candidate in candidates if candidate["eligible"]],
        key=lambda candidate: (-candidate["score"], candidate["agent_name"], candidate["agent_id"]),
    )
    if not eligible:
        summary = "; ".join(
            f"{candidate['agent_name']}: {', '.join(candidate['elimination_reasons'])}"
            for candidate in candidates
        ) or "No enabled Agents"
        raise NoEligibleAgentError(f"No eligible Agent for task '{task_id}': {summary}")

    selected = eligible[0]
    fallback_agents = [candidate["agent_id"] for candidate in eligible[1:4]]
    result = {
        "task_id": task_id,
        "goal_id": goal_id,
        "required_capabilities": required_capabilities,
        "required_tools": required_tools,
        "candidates": candidates,
        "selected_agent_id": selected["agent_id"],
        "selected_model_id": selected["selected_model_id"],
        "backup_model_ids": selected["backup_model_ids"],
        "score": selected["score"],
        "selection_reason": (
            f"{selected['agent_name']} covers all required capabilities/tools with "
            f"{selected['selected_model_name']} and scored {selected['score']:.3f}."
        ),
        "fallback_entry": {
            "agent_ids": fallback_agents,
            "model_ids": selected["backup_model_ids"],
            "handoff_allowed": bool(selected["allow_handoff"] and (fallback_agents or selected["backup_model_ids"])),
            "reason": "Use Handoff for capability, model or quota mismatch without replanning the Goal.",
        },
        "task_type": task_type,
    }
    if persist:
        decision = AgentSelectionDecision(
            id=str(uuid.uuid4()), goal_id=goal_id, task_id=task_id,
            required_capabilities=json.dumps(required_capabilities), required_tools=json.dumps(required_tools),
            candidates=json.dumps(candidates, ensure_ascii=False), selected_agent_id=result["selected_agent_id"],
            selected_model_id=result["selected_model_id"], backup_model_ids=json.dumps(result["backup_model_ids"]),
            score=result["score"], selection_reason=result["selection_reason"],
            fallback_entry=json.dumps(result["fallback_entry"], ensure_ascii=False),
        )
        db.add(decision); db.flush()
        result["id"] = decision.id
    return result


def list_decisions(db: Session, goal_id: str) -> List[dict]:
    return [item.to_dict() for item in db.query(AgentSelectionDecision).filter(
        AgentSelectionDecision.goal_id == goal_id,
    ).order_by(AgentSelectionDecision.created_at.asc()).all()]


def _evaluate_candidate(
    agent: AgentStation, *, models: Dict[str, Model], quotas: Dict[str, str], active_load: int,
    required_capabilities: List[str], required_tools: List[str], risk_level: str,
    workspace_scope: Optional[str], input_type: str, output_type: str,
    context_length_estimate: int, require_model: bool,
) -> Dict:
    profile = capability_profile(agent)
    missing_capabilities = [item for item in required_capabilities if profile.get(item, 0) < 0.5]
    missing_tools = sorted(set(required_tools) - set(allowed_tools(agent)))
    reasons = []
    if missing_capabilities: reasons.append(f"missing capabilities {missing_capabilities}")
    if missing_tools: reasons.append(f"missing tools {missing_tools}")
    if input_type not in agent.get_input_types(): reasons.append(f"unsupported input type {input_type}")
    if output_type not in agent.get_output_types(): reasons.append(f"unsupported output type {output_type}")
    if workspace_scope and not _scope_allowed(workspace_scope, agent.get_workspace_permissions()):
        reasons.append(f"workspace scope {workspace_scope} is not allowed")
    if active_load >= (agent.max_concurrency or 1): reasons.append("concurrency limit reached")

    model_scores = _score_models(
        agent, models=models, quotas=quotas, required_capabilities=required_capabilities,
        context_length_estimate=context_length_estimate,
    )
    if require_model and not model_scores: reasons.append("no enabled model satisfies context/quota constraints")
    selected_model = model_scores[0] if model_scores else {
        "model_id": agent.default_model_id, "model_name": agent.default_model_id,
        "score": 0.5, "cost_fit": 0.5, "speed_fit": 0.5, "quota_fit": 0.5, "context_fit": 0.5,
    }
    proficiency = sum(profile.get(item, 0) for item in required_capabilities) / max(1, len(required_capabilities))
    success_total = agent.total_tasks_completed + agent.total_tasks_failed
    historical = agent.total_tasks_completed / success_total if success_total else 0.5
    load_fit = max(0.0, 1 - active_load / max(1, agent.max_concurrency or 1))
    tool_fit = 1.0 if not missing_tools else 0.0
    risk_fit = 1.0 if risk_level != "high" or profile.get("review", 0) >= 0.5 or profile.get("security_review", 0) >= 0.5 else 0.5
    dimensions = {
        "capability_match": proficiency, "model_fit": selected_model["score"], "tool_fit": tool_fit,
        "context_fit": selected_model["context_fit"], "historical_success": historical,
        "cost_fit": selected_model["cost_fit"], "latency_fit": selected_model["speed_fit"],
        "quota_fit": selected_model["quota_fit"], "risk_policy": risk_fit, "load_fit": load_fit,
    }
    weights = {
        "capability_match": .28, "model_fit": .18, "tool_fit": .10, "context_fit": .08,
        "historical_success": .12, "cost_fit": .07, "latency_fit": .05, "quota_fit": .05,
        "risk_policy": .04, "load_fit": .03,
    }
    score = round(sum(dimensions[key] * weights[key] for key in weights), 4)
    return {
        "agent_id": agent.id, "agent_name": agent.name, "role": agent.role,
        "eligible": not reasons, "elimination_reasons": reasons, "score": score,
        "score_breakdown": {key: round(value, 4) for key, value in dimensions.items()},
        "selected_model_id": selected_model["model_id"], "selected_model_name": selected_model["model_name"],
        "backup_model_ids": [item["model_id"] for item in model_scores[1:4]],
        "model_candidates": model_scores, "current_load": active_load,
        "max_concurrency": agent.max_concurrency, "allow_handoff": agent.allow_handoff,
    }


def _score_models(agent: AgentStation, *, models: Dict[str, Model], quotas: Dict[str, str],
                  required_capabilities: List[str], context_length_estimate: int) -> List[dict]:
    required_model_caps = set().union(*(MODEL_CAPABILITIES.get(item, {"reasoning"}) for item in required_capabilities))
    configured_ids = list(dict.fromkeys([agent.default_model_id, *agent.get_backup_model_ids()]))
    scored = []
    for model_id in configured_ids:
        model = models.get(model_id)
        quota = quotas.get(model_id, "normal")
        if not model or quota in {"limited", "cooldown"} or model.max_context_tokens < context_length_estimate * 1.2:
            continue
        tags = set(model.get_capability_tags())
        capability_fit = len(required_model_caps & tags) / max(1, len(required_model_caps))
        context_fit = min(1.0, model.max_context_tokens / max(1, context_length_estimate * 4))
        cost_fit = (6 - model.cost_level) / 5
        speed_fit = (6 - model.speed_level) / 5
        quota_fit = {"normal": 1.0, "warning": .7, "near_limit": .4, "unknown": .8}.get(quota, .8)
        default_bonus = .08 if model.id == agent.default_model_id else 0
        score = min(1.0, capability_fit * .4 + context_fit * .2 + cost_fit * .13 + speed_fit * .12 + quota_fit * .15 + default_bonus)
        scored.append({
            "model_id": model.id, "model_name": model.display_name, "score": round(score, 4),
            "capability_fit": round(capability_fit, 4), "context_fit": round(context_fit, 4),
            "cost_fit": round(cost_fit, 4), "speed_fit": round(speed_fit, 4),
            "quota_fit": round(quota_fit, 4), "quota_status": quota,
        })
    return sorted(scored, key=lambda item: (-item["score"], item["model_id"]))


def _scope_allowed(requested: str, permissions: List[str]) -> bool:
    if not permissions:
        return True
    return any(permission in {"*", "**"} or fnmatch.fnmatch(requested, permission) or fnmatch.fnmatch(permission, requested) for permission in permissions)
