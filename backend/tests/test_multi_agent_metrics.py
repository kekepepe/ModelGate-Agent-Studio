import uuid

from src.models.workspace import ExecutionPlan, Goal, PlanTask, Task
from src.services import multi_agent_metrics_service, runtime_service


def test_parallel_benefit_subtracts_coordination_cost_from_serial_baseline(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Frontend and backend", status="completed")
    plan = ExecutionPlan(
        id=str(uuid.uuid4()), plan_id=str(uuid.uuid4()), goal_id=goal.id, version=1,
        status="active", task_mode="parallel_multi_agent", goal_summary=goal.title,
        activation_reason="Independent frontend and backend branches can run in parallel.",
        planner_type="rule_fallback",
    )
    tasks = [
        Task(id="plan", goal_id=goal.id, title="Plan", task_type="planning", status="completed", tokens_used=50, duration_ms=200, assigned_agent_id="planner"),
        Task(id="front", goal_id=goal.id, title="Frontend", task_type="coding", status="completed_verified", tokens_used=100, duration_ms=1000, assigned_agent_id="front-agent"),
        Task(id="back", goal_id=goal.id, title="Backend", task_type="coding", status="completed_verified", tokens_used=120, duration_ms=800, assigned_agent_id="back-agent"),
        Task(id="merge", goal_id=goal.id, title="Merge", task_type="merge", status="completed_verified", tokens_used=30, duration_ms=100, assigned_agent_id="merge-agent"),
        Task(id="verify", goal_id=goal.id, title="Verify", task_type="verification", status="completed_verified", tokens_used=20, duration_ms=100, assigned_agent_id="reviewer"),
    ]
    plan_tasks = [
        PlanTask(id=str(uuid.uuid4()), plan_version_id=plan.id, client_task_id="front", objective="Frontend", task_type="coding", parallel_safe=True, runtime_task_id="front"),
        PlanTask(id=str(uuid.uuid4()), plan_version_id=plan.id, client_task_id="back", objective="Backend", task_type="coding", parallel_safe=True, runtime_task_id="back"),
    ]
    db_session.add_all([goal, plan, *tasks, *plan_tasks]); db_session.commit()

    metrics = multi_agent_metrics_service.calculate(plan, plan_tasks, tasks)
    assert metrics["single_agent_serial_baseline_ms"] == 1800
    assert metrics["parallel_observed_estimate_ms"] == 1000
    assert metrics["potential_parallel_saving_ms"] == 800
    assert metrics["coordination_duration_ms"] == 400
    assert metrics["estimated_net_time_benefit_ms"] == 400
    assert metrics["coordination_tokens"] == 100
    assert metrics["benefit_positive"] is True
    assert metrics["mode_comparison"] == {
        "single_agent": {"duration_ms": 1800, "tokens": 220, "basis": "Productive Task durations/tokens without recorded coordination work."},
        "sequential_multi_agent": {"duration_ms": 2200, "tokens": 320, "basis": "All recorded Task durations summed serially."},
        "parallel_multi_agent": {"duration_ms": 1400, "tokens": 320, "basis": "Parallel-safe durations collapsed to their maximum; other work remains serial."},
    }

    summary = runtime_service._build_final_summary(db_session, goal, tasks, 0)
    assert summary["multi_agent"]["why_multi_agent"] == plan.activation_reason
    assert summary["multi_agent"]["measurement_note"].startswith("Time benefit compares")
