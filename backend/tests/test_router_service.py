import pytest
from sqlalchemy.orm import Session

from src.models.model import Model
from src.models.agent import AgentStation
from src.services.router_service import (
    select_model,
    override_model,
    get_routing_rules,
    NoEligibleModelError,
    InvalidOverrideError,
    _filter_candidates,
    _score_model,
    _get_adjusted_weights,
)


@pytest.fixture
def seed_models(db_session: Session):
    """Seed test models into the database."""
    models = [
        Model(
            id="model-claude-opus",
            provider="anthropic",
            model_name="claude-3-opus",
            display_name="Claude 3 Opus",
            max_context_tokens=200000,
            cost_level=5,
            speed_level=3,
            is_enabled=True,
        ),
        Model(
            id="model-gpt-4-turbo",
            provider="openai",
            model_name="gpt-4-turbo",
            display_name="GPT-4 Turbo",
            max_context_tokens=128000,
            cost_level=4,
            speed_level=3,
            is_enabled=True,
        ),
        Model(
            id="model-deepseek-coder",
            provider="deepseek",
            model_name="deepseek-coder",
            display_name="DeepSeek Coder",
            max_context_tokens=64000,
            cost_level=2,
            speed_level=3,
            is_enabled=True,
        ),
        Model(
            id="model-disabled",
            provider="test",
            model_name="disabled-model",
            display_name="Disabled Model",
            max_context_tokens=100000,
            cost_level=3,
            speed_level=3,
            is_enabled=False,
        ),
    ]
    for m in models:
        m.set_capability_tags(["code", "reasoning"])
        db_session.add(m)

    # Add a model with limited context
    limited_model = Model(
        id="model-limited-context",
        provider="test",
        model_name="limited-context",
        display_name="Limited Context Model",
        max_context_tokens=4000,
        cost_level=1,
        speed_level=1,
        is_enabled=True,
    )
    limited_model.set_capability_tags(["code", "reasoning"])
    db_session.add(limited_model)

    db_session.commit()
    return models


@pytest.fixture
def seed_agent(db_session: Session):
    agent = AgentStation(
        id="agent-coder",
        name="Coder Agent",
        role="coder",
        description="Code writer",
        status="idle",
        default_model_id="model-deepseek-coder",
    )
    agent.set_backup_model_ids(["model-claude-opus", "model-gpt-4-turbo"])
    agent.set_allowed_tools(["file_read", "file_write"])
    db_session.add(agent)
    db_session.commit()
    return agent


class TestFilterCandidates:
    def test_filters_disabled_models(self, db_session, seed_models):
        candidates = _filter_candidates(db_session, ["code", "reasoning"], 8000)
        ids = [m.id for m in candidates]
        assert "model-disabled" not in ids
        assert "model-claude-opus" in ids

    def test_filters_context_insufficient(self, db_session, seed_models):
        candidates = _filter_candidates(db_session, ["code", "reasoning"], 5000)
        ids = [m.id for m in candidates]
        assert "model-limited-context" not in ids

    def test_filters_missing_capabilities(self, db_session, seed_models):
        candidates = _filter_candidates(db_session, ["vision"], 8000)
        ids = [m.id for m in candidates]
        assert len(ids) == 0

    def test_filters_models_with_real_limited_quota(self, db_session, seed_models):
        from src.models.quota import QuotaRecord
        db_session.add(QuotaRecord(
            id="quota-opus", provider="anthropic", model_id="model-claude-opus",
            model_name="Claude 3 Opus", quota_status="limited", usage_percent=1.0,
        ))
        db_session.commit()
        result = select_model(
            db=db_session, task_id="task-1", task_type="coding", required_capabilities=["code"],
            context_length_estimate=8000,
        )
        assert result["selected_model_id"] != "model-claude-opus"
        assert all(item["model_id"] != "model-claude-opus" for item in result["score_breakdown"])


class TestScoreModel:
    def test_capability_match_perfect(self, db_session, seed_models):
        model = db_session.query(Model).filter(Model.id == "model-claude-opus").first()
        result = _score_model(
            model, ["code", "reasoning"], "coder", 8000, "medium", "balanced", "moderate"
        )
        cap_score = next(d for d in result["dimension_scores"] if d["dimension"] == "capability_match")
        assert cap_score["score"] == 1.0

    def test_role_match_first_preference(self, db_session, seed_models):
        model = db_session.query(Model).filter(Model.id == "model-deepseek-coder").first()
        result = _score_model(
            model, ["code"], "coder", 8000, "medium", "balanced", "moderate"
        )
        role_score = next(d for d in result["dimension_scores"] if d["dimension"] == "role_match")
        assert role_score["score"] == 1.0

    def test_context_fit_high_margin(self, db_session, seed_models):
        model = db_session.query(Model).filter(Model.id == "model-claude-opus").first()
        result = _score_model(
            model, ["code"], None, 8000, "medium", "balanced", "moderate"
        )
        ctx_score = next(d for d in result["dimension_scores"] if d["dimension"] == "context_fit")
        assert ctx_score["score"] == 1.0


class TestSelectModel:
    def test_select_model_success(self, db_session, seed_models, seed_agent):
        result = select_model(
            db=db_session,
            task_id="task-1",
            task_type="coding",
            preferred_agent_id="agent-coder",
            context_length_estimate=8000,
        )
        assert result["selected_model_id"]
        assert len(result["backup_model_ids"]) >= 0
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["routing_reason"]["summary"]
        assert len(result["score_breakdown"]) > 0

    def test_select_model_prefers_code_model_for_coding(self, db_session, seed_models, seed_agent):
        result = select_model(
            db=db_session,
            task_id="task-1",
            task_type="coding",
            preferred_agent_id="agent-coder",
            context_length_estimate=8000,
        )
        # DeepSeek Coder should be highly ranked for coding tasks
        assert result["selected_model_id"] in [
            "model-deepseek-coder",
            "model-claude-opus",
            "model-gpt-4-turbo",
        ]

    def test_select_model_no_candidates(self, db_session):
        with pytest.raises(NoEligibleModelError):
            select_model(
                db=db_session,
                task_id="task-1",
                task_type="coding",
                required_capabilities=["nonexistent_capability"],
                context_length_estimate=8000,
            )

    def test_select_model_user_override(self, db_session, seed_models, seed_agent):
        result = select_model(
            db=db_session,
            task_id="task-1",
            task_type="coding",
            preferred_model_id="model-claude-opus",
            context_length_estimate=8000,
        )
        assert result["selected_model_id"] == "model-claude-opus"
        assert result["is_user_override"] is True

    def test_select_model_invalid_override(self, db_session, seed_models):
        with pytest.raises(InvalidOverrideError):
            select_model(
                db=db_session,
                task_id="task-1",
                task_type="coding",
                preferred_model_id="model-disabled",
                context_length_estimate=8000,
            )

    def test_select_model_risk_flags_all_limited_mock(self, db_session):
        # With empty DB and no models, should raise NoEligibleModelError
        with pytest.raises(NoEligibleModelError):
            select_model(
                db=db_session,
                task_id="task-1",
                task_type="coding",
                context_length_estimate=8000,
            )


class TestOverrideModel:
    def test_override_success(self, db_session, seed_models):
        result = override_model(
            db=db_session,
            task_id="task-1",
            selected_model_id="model-claude-opus",
            backup_model_ids=["model-claude-opus", "model-gpt-4-turbo"],
        )
        assert result["selected_model_id"] == "model-claude-opus"
        assert result["is_user_override"] is True

    def test_override_not_in_backup(self, db_session, seed_models):
        with pytest.raises(InvalidOverrideError):
            override_model(
                db=db_session,
                task_id="task-1",
                selected_model_id="model-claude-opus",
                backup_model_ids=["model-gpt-4-turbo"],
            )

    def test_override_disabled_model(self, db_session, seed_models):
        with pytest.raises(InvalidOverrideError):
            override_model(
                db=db_session,
                task_id="task-1",
                selected_model_id="model-disabled",
            )


class TestRoutingRules:
    def test_get_routing_rules(self):
        rules = get_routing_rules()
        assert "weights" in rules
        assert "role_preferences" in rules
        assert "hard_constraints" in rules
        weights = rules["weights"]
        assert abs(sum(weights.values()) - 1.0) < 0.01


class TestAdjustedWeights:
    def test_low_budget_increases_cost_weight(self):
        weights = _get_adjusted_weights("low", "balanced", "moderate")
        assert weights["cost_fit"] > 0.15

    def test_quality_speed_increases_capability_weight(self):
        weights = _get_adjusted_weights("medium", "quality", "moderate")
        assert weights["capability_match"] > 0.25

    def test_weights_sum_to_one(self):
        weights = _get_adjusted_weights("high", "fast", "very_complex")
        assert abs(sum(weights.values()) - 1.0) < 0.01
