from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from src.models.model import Model
from src.models.agent import AgentStation
from src.models.quota import QuotaRecord
from src.data.models import (
    ROLE_MODEL_PREFERENCES,
    TASK_TYPE_CAPABILITIES,
    DEFAULT_WEIGHTS,
    QUOTA_HEALTH_SCORES,
    get_model_seed,
)


class RouterServiceError(Exception):
    pass


class NoEligibleModelError(RouterServiceError):
    pass


class InvalidOverrideError(RouterServiceError):
    pass


def _get_required_capabilities(task_type: str, requires_tool_calling: bool) -> List[str]:
    caps = set(TASK_TYPE_CAPABILITIES.get(task_type, ["reasoning"]))
    if requires_tool_calling:
        caps.add("tool_calling")
    return list(caps)


def _get_quota_statuses(db: Session) -> Dict[str, str]:
    """Read Quota Manager state once per routing decision.

    Models without a record remain usable as `normal` for backward compatibility
    with local and mock providers, while configured LIMITED/COOLDOWN models are
    excluded before scoring.
    """
    return {record.model_id: record.quota_status for record in db.query(QuotaRecord).all()}


def _quota_status(model_id: str, quota_statuses: Optional[Dict[str, str]] = None) -> str:
    return (quota_statuses or {}).get(model_id, "normal")


def _filter_candidates(
    db: Session,
    required_capabilities: List[str],
    context_length_estimate: int,
    preferred_model_id: Optional[str] = None,
    quota_statuses: Optional[Dict[str, str]] = None,
) -> List[Model]:
    """Hard constraint filtering."""
    all_models = db.query(Model).filter(Model.is_enabled == True).all()
    candidates = []
    excluded_reasons = []

    for m in all_models:
        # 1. Check real quota status when it is configured.
        quota_status = _quota_status(m.id, quota_statuses)
        if quota_status in ("limited", "cooldown"):
            excluded_reasons.append(f"{m.display_name}: quota {quota_status}")
            continue

        # 2. Check context window
        if m.max_context_tokens < context_length_estimate * 1.2:
            excluded_reasons.append(
                f"{m.display_name}: context {m.max_context_tokens} < {context_length_estimate * 1.2}"
            )
            continue

        # 3. Check required capabilities
        model_caps = set(m.get_capability_tags())
        missing = [cap for cap in required_capabilities if cap not in model_caps]
        if missing:
            excluded_reasons.append(f"{m.display_name}: missing capabilities {missing}")
            continue

        candidates.append(m)

    return candidates


def _compute_capability_match(model: Model, required_capabilities: List[str]) -> float:
    if not required_capabilities:
        return 0.5
    model_caps = set(model.get_capability_tags())
    matched = sum(1 for cap in required_capabilities if cap in model_caps)
    return min(matched / len(required_capabilities), 1.0)


def _compute_role_match(model: Model, agent_role: Optional[str]) -> float:
    if not agent_role:
        return 0.5
    prefs = ROLE_MODEL_PREFERENCES.get(agent_role, [])
    if model.id in prefs:
        rank = prefs.index(model.id)
        # 1st = 1.0, 2nd = 0.85, 3rd = 0.70
        return max(1.0 - rank * 0.15, 0.5)
    return 0.5


def _compute_context_fit(model: Model, context_length_estimate: int) -> float:
    if model.max_context_tokens <= 0:
        return 0.0
    margin_ratio = (model.max_context_tokens - context_length_estimate) / model.max_context_tokens
    if margin_ratio > 0.5:
        return 1.0
    elif margin_ratio > 0.2:
        return 0.8
    elif margin_ratio > 0.0:
        return 0.6
    return 0.0


def _compute_cost_fit(model: Model, budget_preference: str) -> float:
    # cost_level: 1=cheapest, 5=most expensive
    base = (6 - model.cost_level) / 5.0
    if budget_preference == "low" and model.cost_level > 3:
        base -= 0.2
    elif budget_preference == "high" and model.cost_level < 3:
        base += 0.05
    return max(min(base, 1.0), 0.0)


def _compute_speed_fit(model: Model, speed_preference: str) -> float:
    # speed_level: 1=fastest, 5=slowest
    base = (6 - model.speed_level) / 5.0
    if speed_preference == "fast" and model.speed_level > 3:
        base -= 0.2
    elif speed_preference == "quality" and model.speed_level < 3:
        base += 0.05
    return max(min(base, 1.0), 0.0)


def _compute_quota_health(model: Model, quota_statuses: Optional[Dict[str, str]] = None) -> float:
    quota_status = _quota_status(model.id, quota_statuses)
    return QUOTA_HEALTH_SCORES.get(quota_status, 0.8)


def _get_adjusted_weights(
    budget_preference: str,
    speed_preference: str,
    task_complexity: str,
) -> Dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)

    if budget_preference == "low":
        weights["cost_fit"] = weights.get("cost_fit", 0.15) + 0.10
        weights["capability_match"] = weights.get("capability_match", 0.25) - 0.05
    elif budget_preference == "high":
        weights["cost_fit"] = weights.get("cost_fit", 0.15) - 0.05
        weights["capability_match"] = weights.get("capability_match", 0.25) + 0.05

    if speed_preference == "fast":
        weights["speed_fit"] = weights.get("speed_fit", 0.10) + 0.10
        weights["capability_match"] = weights.get("capability_match", 0.25) - 0.05
    elif speed_preference == "quality":
        weights["capability_match"] = weights.get("capability_match", 0.25) + 0.10
        weights["speed_fit"] = weights.get("speed_fit", 0.10) - 0.05

    if task_complexity == "very_complex":
        weights["capability_match"] = weights.get("capability_match", 0.25) + 0.10
        weights["cost_fit"] = weights.get("cost_fit", 0.15) - 0.05
    elif task_complexity == "simple":
        weights["cost_fit"] = weights.get("cost_fit", 0.15) + 0.05
        weights["capability_match"] = weights.get("capability_match", 0.25) - 0.05

    # Normalize to sum ≈ 1.0
    total = sum(weights.values())
    if total > 0:
        weights = {k: round(v / total, 4) for k, v in weights.items()}
    return weights


def _score_model(
    model: Model,
    required_capabilities: List[str],
    agent_role: Optional[str],
    context_length_estimate: int,
    budget_preference: str,
    speed_preference: str,
    task_complexity: str,
    default_model_id: Optional[str] = None,
    quota_statuses: Optional[Dict[str, str]] = None,
) -> Dict:
    weights = _get_adjusted_weights(budget_preference, speed_preference, task_complexity)

    capability_match = _compute_capability_match(model, required_capabilities)
    role_match = _compute_role_match(model, agent_role)
    context_fit = _compute_context_fit(model, context_length_estimate)
    cost_fit = _compute_cost_fit(model, budget_preference)
    speed_fit = _compute_speed_fit(model, speed_preference)
    quota_health = _compute_quota_health(model, quota_statuses)

    # Historical performance mock (MVP-B)
    historical_performance = 0.5

    dimensions = {
        "capability_match": capability_match,
        "role_match": role_match,
        "context_fit": context_fit,
        "cost_fit": cost_fit,
        "speed_fit": speed_fit,
        "quota_health": quota_health,
        "historical_performance": historical_performance,
    }

    total_score = 0.0
    dimension_scores = []
    for dim, score in dimensions.items():
        w = weights.get(dim, 0.0)
        weighted = round(score * w, 4)
        total_score += weighted
        dimension_scores.append({
            "dimension": dim,
            "score": round(score, 4),
            "weight": w,
            "weighted_score": weighted,
            "reason": _dimension_reason(dim, score, model),
        })

    # Agent default_model_id bonus: +15% if model is the agent's default
    if default_model_id and model.id == default_model_id:
        total_score = min(round(total_score + 0.15, 4), 1.0)

    return {
        "total_score": round(total_score, 4),
        "dimension_scores": dimension_scores,
        "weights": weights,
    }


def _dimension_reason(dimension: str, score: float, model: Model) -> str:
    reasons = {
        "capability_match": f"匹配度 {int(score * 100)}%" if score > 0.5 else "能力标签匹配较低",
        "role_match": f"角色偏好排名第 {int((1 - score) / 0.15) + 1}" if score >= 0.7 else "非首选角色匹配",
        "context_fit": f"上下文余量充足" if score >= 0.8 else "上下文余量一般",
        "cost_fit": f"成本等级 {model.cost_level}" if score > 0.5 else "成本较高",
        "speed_fit": f"速度等级 {model.speed_level}" if score > 0.5 else "速度较慢",
        "quota_health": "额度健康" if score >= 0.8 else "额度接近限制",
        "historical_performance": "暂无历史数据" if score == 0.5 else "历史表现良好",
    }
    return reasons.get(dimension, "")


def _generate_routing_reason(
    selected_model: Model,
    score_info: Dict,
    agent_role: Optional[str],
    task_type: str,
    backup_models: List[Model],
    quota_status: str = "normal",
) -> Dict:
    primary = []
    secondary = []
    tradeoffs = []

    # Identify top-scoring dimension
    top_dim = max(score_info["dimension_scores"], key=lambda d: d["weighted_score"])
    dim_name_map = {
        "capability_match": "能力匹配度",
        "role_match": "角色匹配度",
        "context_fit": "上下文适配度",
        "cost_fit": "成本适配度",
        "speed_fit": "速度适配度",
        "quota_health": "额度健康度",
        "historical_performance": "历史表现",
    }

    primary.append(
        f"{selected_model.display_name} 在 {dim_name_map.get(top_dim['dimension'], top_dim['dimension'])} 维度表现最优"
    )

    if agent_role:
        role_prefs = ROLE_MODEL_PREFERENCES.get(agent_role, [])
        if selected_model.id in role_prefs:
            rank = role_prefs.index(selected_model.id) + 1
            primary.append(f"在 {agent_role} 角色偏好中排名第 {rank}")

    if top_dim["dimension"] == "capability_match":
        task_type_names = {
            "coding": "编码任务",
            "planning": "规划任务",
            "research": "调研任务",
            "review": "审查任务",
            "summarization": "摘要任务",
            "supervision": "监督任务",
            "debugging": "调试任务",
            "documentation": "文档任务",
            "testing": "测试任务",
            "general": "通用任务",
        }
        primary.append(f"{task_type_names.get(task_type, task_type)} 优先选择 {selected_model.display_name}")

    secondary.append(f"上下文窗口 {selected_model.max_context_tokens}，充足")
    secondary.append(f"额度状态：{quota_status}")

    if selected_model.cost_level >= 4:
        tradeoffs.append(f"成本较高（等级 {selected_model.cost_level}）")
    if selected_model.speed_level >= 4:
        tradeoffs.append(f"响应速度较慢（等级 {selected_model.speed_level}）")

    return {
        "summary": f"{selected_model.display_name} 被选为 {task_type} 任务的首选模型",
        "primary_factors": primary,
        "secondary_factors": secondary,
        "tradeoffs": tradeoffs,
    }


def _build_risk_flags(
    selected_model: Model,
    all_scores: List[Dict],
    candidates: List[Model],
    agent_default_model_id: Optional[str] = None,
    quota_statuses: Optional[Dict[str, str]] = None,
) -> List[Dict]:
    flags = []

    quota_status = _quota_status(selected_model.id, quota_statuses)
    if quota_status == "warning":
        flags.append({
            "type": "quota_warning",
            "severity": "medium",
            "message": f"{selected_model.display_name} 额度使用率较高，建议关注",
            "suggestion": "系统已自动设置备用模型",
        })
    elif quota_status == "near_limit":
        flags.append({
            "type": "quota_warning",
            "severity": "high",
            "message": f"{selected_model.display_name} 额度接近限制",
            "suggestion": "建议尽快切换至备用模型",
        })

    # Check if top 2 scores are very close
    if len(all_scores) >= 2:
        sorted_scores = sorted(all_scores, key=lambda s: s["total_score"], reverse=True)
        gap = sorted_scores[0]["total_score"] - sorted_scores[1]["total_score"]
        if gap < 0.05:
            flags.append({
                "type": "low_confidence",
                "severity": "low",
                "message": "多个模型评分接近，建议关注表现",
                "suggestion": None,
            })

    # Default model unavailable
    if agent_default_model_id:
        candidate_ids = {m.id for m in candidates}
        if agent_default_model_id not in candidate_ids:
            flags.append({
                "type": "default_model_unavailable",
                "severity": "medium",
                "message": "默认模型不可用，已自动选择备用模型",
                "suggestion": "请检查默认模型的额度或配置状态",
            })

    # Context limit warning (margin is tight but not excluded)
    # Models passing filter have context >= estimate * 1.2, so margin_ratio >= 0.167
    # Warn if margin_ratio is below 0.3 (context window less than 1.43x estimate)
    if selected_model.max_context_tokens > 0:
        # We don't have context_length_estimate here; skip precise context_limit flag
        pass

    # Cost high warning
    if selected_model.cost_level >= 4:
        flags.append({
            "type": "cost_high",
            "severity": "low",
            "message": f"{selected_model.display_name} 成本较高（等级 {selected_model.cost_level}）",
            "suggestion": "如预算敏感，可切换至备用模型",
        })

    # Speed slow warning
    if selected_model.speed_level >= 4:
        flags.append({
            "type": "speed_slow",
            "severity": "low",
            "message": f"{selected_model.display_name} 响应速度较慢（等级 {selected_model.speed_level}）",
            "suggestion": "如对速度敏感，可切换至更快的备用模型",
        })

    if not candidates:
        flags.append({
            "type": "quota_warning",
            "severity": "high",
            "message": "没有可用的模型",
            "suggestion": "请检查模型配置或额度状态",
        })

    return flags


def select_model(
    db: Session,
    task_id: str,
    task_type: str,
    task_complexity: str = "moderate",
    task_description: Optional[str] = None,
    required_capabilities: Optional[List[str]] = None,
    preferred_agent_id: Optional[str] = None,
    preferred_model_id: Optional[str] = None,
    context_length_estimate: int = 8000,
    has_vision_input: bool = False,
    requires_tool_calling: bool = False,
    budget_preference: str = "medium",
    speed_preference: str = "balanced",
) -> Dict:
    quota_statuses = _get_quota_statuses(db)
    # 1. Resolve required capabilities
    caps = required_capabilities or _get_required_capabilities(task_type, requires_tool_calling)
    if has_vision_input:
        caps = list(set(caps + ["vision"]))

    # 2. Resolve agent role and default model
    agent_role = None
    agent_default_model_id = None
    if preferred_agent_id:
        agent = db.query(AgentStation).filter(AgentStation.id == preferred_agent_id).first()
        if agent:
            agent_role = agent.role
            agent_default_model_id = agent.default_model_id

    # 3. User override: if preferred_model_id is set and valid, use it directly
    if preferred_model_id:
        model = db.query(Model).filter(Model.id == preferred_model_id, Model.is_enabled == True).first()
        if model:
            # Still check hard constraints
            quota_status = _quota_status(model.id, quota_statuses)
            if quota_status in ("limited", "cooldown"):
                raise InvalidOverrideError(f"模型 {model.display_name} 当前不可用（额度 {quota_status}）")
            if model.max_context_tokens < context_length_estimate * 1.2:
                raise InvalidOverrideError(f"模型 {model.display_name} 上下文窗口不足")
            missing_caps = [cap for cap in caps if cap not in model.get_capability_tags()]
            if missing_caps:
                raise InvalidOverrideError(f"模型 {model.display_name} 缺少必需能力: {missing_caps}")

            score_info = _score_model(
                model, caps, agent_role, context_length_estimate,
                budget_preference, speed_preference, task_complexity,
                default_model_id=agent_default_model_id,
                quota_statuses=quota_statuses,
            )
            return {
                "selected_model_id": model.id,
                "selected_agent_id": preferred_agent_id,
                "backup_model_ids": [],
                "routing_reason": {
                    "summary": f"用户手动指定 {model.display_name}",
                    "primary_factors": ["用户手动覆盖路由决策"],
                    "secondary_factors": [],
                    "tradeoffs": [],
                },
                "confidence": 1.0,
                "risk_flags": [],
                "score_breakdown": [{
                    "model_id": model.id,
                    "model_name": model.display_name,
                    "total_score": score_info["total_score"],
                    "dimension_scores": score_info["dimension_scores"],
                }],
                "is_user_override": True,
                "override_note": "用户手动指定模型",
            }
        else:
            raise InvalidOverrideError(f"模型 {preferred_model_id} 不存在或未启用")

    # 4. Filter candidates
    candidates = _filter_candidates(db, caps, context_length_estimate, quota_statuses=quota_statuses)
    if not candidates:
        raise NoEligibleModelError("没有可用的模型，请检查模型配置或额度状态")

    # 5. Score all candidates
    scored = []
    for model in candidates:
        score_info = _score_model(
            model, caps, agent_role, context_length_estimate,
            budget_preference, speed_preference, task_complexity,
            default_model_id=agent_default_model_id,
            quota_statuses=quota_statuses,
        )
        scored.append({
            "model": model,
            "total_score": score_info["total_score"],
            "dimension_scores": score_info["dimension_scores"],
        })

    # 6. Sort by total score descending
    scored.sort(key=lambda s: s["total_score"], reverse=True)

    # 7. Select top model and backups
    selected = scored[0]
    backups = scored[1:4]  # up to 3 backups

    # 8. Compute confidence
    confidence = selected["total_score"]
    if len(scored) >= 2:
        gap = scored[0]["total_score"] - scored[1]["total_score"]
        if gap < 0.05:
            confidence *= 0.85
    confidence = round(min(confidence, 1.0), 4)

    # 9. Build result
    routing_reason = _generate_routing_reason(
        selected["model"], selected, agent_role, task_type,
        [s["model"] for s in backups],
        quota_status=_quota_status(selected["model"].id, quota_statuses),
    )
    risk_flags = _build_risk_flags(selected["model"], scored, candidates, agent_default_model_id, quota_statuses)

    score_breakdown = []
    for s in scored:
        score_breakdown.append({
            "model_id": s["model"].id,
            "model_name": s["model"].display_name,
            "total_score": s["total_score"],
            "dimension_scores": s["dimension_scores"],
        })

    return {
        "selected_model_id": selected["model"].id,
        "selected_agent_id": preferred_agent_id,
        "backup_model_ids": [s["model"].id for s in backups],
        "routing_reason": routing_reason,
        "confidence": confidence,
        "risk_flags": risk_flags,
        "score_breakdown": score_breakdown,
        "is_user_override": False,
        "override_note": None,
    }


def override_model(
    db: Session,
    task_id: str,
    selected_model_id: str,
    original_model_id: Optional[str] = None,
    reason: Optional[str] = None,
    backup_model_ids: Optional[List[str]] = None,
) -> Dict:
    """Validate and record a user model override."""
    # Check model exists and is enabled
    model = db.query(Model).filter(Model.id == selected_model_id, Model.is_enabled == True).first()
    if not model:
        raise InvalidOverrideError(f"模型 {selected_model_id} 不存在或未启用")

    # Check quota
    quota_status = _quota_status(model.id, _get_quota_statuses(db))
    if quota_status in ("limited", "cooldown"):
        raise InvalidOverrideError(f"模型 {model.display_name} 当前不可用（额度 {quota_status}）")

    # Check backup list if provided
    if backup_model_ids and selected_model_id not in backup_model_ids:
        raise InvalidOverrideError("只能切换至备用模型列表中的模型")

    return {
        "task_id": task_id,
        "selected_model_id": selected_model_id,
        "is_user_override": True,
        "override_note": reason or "用户手动切换模型",
    }


def get_routing_rules() -> Dict:
    return {
        "weights": DEFAULT_WEIGHTS,
        "role_preferences": ROLE_MODEL_PREFERENCES,
        "hard_constraints": [
            "模型必须已启用 (is_enabled = true)",
            "模型额度状态不能为 LIMITED 或 COOLDOWN",
            "模型上下文窗口必须满足任务需求",
            "模型必须支持任务所需的全部能力标签",
        ],
    }
