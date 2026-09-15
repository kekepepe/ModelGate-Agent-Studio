"""V1.3 P2 T4: real cost accounting.

record_usage accumulates USD cost from Model pricing onto the quota
record; model_call logs carry per-call cost_usd; the FinalSummary
aggregates real per-goal spend and keeps the honest-unavailable stance
when models are unpriced.
"""
import uuid

import pytest

from src.models.handoff import ExecutionLog
from src.models.model import Model
from src.models.quota import QuotaRecord
from src.models.workspace import Goal, Task
from src.services import quota_service
from src.services.runtime_service import _build_final_summary


def _priced_model(db_session, **prices):
    model = Model(
        id=str(uuid.uuid4()), provider="openai", model_name="gpt-priced",
        display_name="GPT Priced", is_enabled=True,
    )
    for key, value in prices.items():
        setattr(model, key, value)
    db_session.add(model)
    db_session.commit()
    return model


def test_record_usage_accumulates_real_cost(db_session):
    model = _priced_model(db_session, price_input=3.0, price_output=15.0)

    first = quota_service.record_usage(
        db=db_session, provider=model.provider, model_id=model.id,
        model_name=model.model_name,
        request_tokens=1_000_000, response_tokens=0, total_tokens=1_000_000,
    )
    assert first["cost_usd"] == pytest.approx(3.0)
    assert first["total_cost_usd"] == pytest.approx(3.0)

    second = quota_service.record_usage(
        db=db_session, provider=model.provider, model_id=model.id,
        model_name=model.model_name,
        request_tokens=0, response_tokens=1_000_000, total_tokens=1_000_000,
    )
    assert second["cost_usd"] == pytest.approx(15.0)
    assert second["total_cost_usd"] == pytest.approx(18.0)

    record = db_session.query(QuotaRecord).filter(QuotaRecord.model_id == model.id).one()
    assert record.total_cost_usd == pytest.approx(18.0)


def test_record_usage_unpriced_model_keeps_cost_none(db_session):
    model = _priced_model(db_session)  # no prices configured

    result = quota_service.record_usage(
        db=db_session, provider=model.provider, model_id=model.id,
        request_tokens=1000, response_tokens=500, total_tokens=1500,
    )
    assert result["cost_usd"] is None
    record = db_session.query(QuotaRecord).filter(QuotaRecord.model_id == model.id).one()
    assert record.total_cost_usd is None


def test_final_summary_aggregates_real_cost(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Priced goal", status="completed")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Do work", status="completed_unverified")
    db_session.add_all([goal, task])
    db_session.flush()

    priced = _priced_model(db_session, price_input=3.0, price_output=15.0)
    unpriced = _priced_model(db_session, price_input=None, price_output=None)

    # Two priced model_call logs + one unpriced (cost None → excluded).
    for model, cost in ((priced, 0.5), (priced, 0.25), (unpriced, None)):
        log = ExecutionLog(
            goal_id=goal.id, task_id=task.id, model_id=model.id,
            event_type="model_call", event_status="completed",
            cost_usd=cost,
        )
        log.set_token_usage({"input_tokens": 1, "output_tokens": 1, "total_tokens": 2})
        db_session.add(log)
    db_session.commit()

    summary = _build_final_summary(db_session, goal, [task], handoff_count=0)

    assert summary["cost"]["available"] is True
    assert summary["cost"]["currency_estimate"] == pytest.approx(0.75)
    cost_by_id = {m["id"]: m["cost_usd"] for m in summary["models"]}
    assert cost_by_id[priced.id] == pytest.approx(0.75)
    assert cost_by_id[unpriced.id] is None


def test_final_summary_stays_honest_without_pricing(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Unpriced goal", status="completed")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Do work", status="completed_unverified")
    unpriced = _priced_model(db_session)
    db_session.add_all([goal, task])
    db_session.flush()
    log = ExecutionLog(
        goal_id=goal.id, task_id=task.id, model_id=unpriced.id,
        event_type="model_call", event_status="completed", cost_usd=None,
    )
    db_session.add(log)
    db_session.commit()

    summary = _build_final_summary(db_session, goal, [task], handoff_count=0)

    assert summary["cost"]["available"] is False
    assert summary["cost"]["currency_estimate"] is None

