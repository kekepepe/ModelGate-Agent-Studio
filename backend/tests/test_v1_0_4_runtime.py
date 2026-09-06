"""V1.0-4 Runtime Engine acceptance tests.

Per 2026-09-06-platform-redesign.md §6.3, the runtime must:

  1. Execute Goal -> Task -> Worker -> Model -> Final Summary
  2. Honour the explicit state machine (no illegal transitions)
  3. Be reachable through the design-documented import path
     `src.runtime.*` (entry layer added in V1.0-4)
  4. Coexist with V1.0-3 Station fields (slug / is_builtin / handoff_policy)
     without breaking runtime behaviour

This file is intentionally small: it complements the existing 8
test_runtime_*.py files. Where they test the engine, these tests
test the *contract the new design promises*.
"""

import uuid

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# (1) src.runtime entry layer is reachable
# ---------------------------------------------------------------------------

class TestRuntimeEntryLayer:
    def test_src_runtime_state_machine_re_exports(self):
        """The state machine must be reachable via src.runtime."""
        from src.runtime import (
            GOAL_TRANSITIONS,
            TASK_TRANSITIONS,
            InvalidStateTransition,
            install_state_guards,
            transition_goal,
            transition_task,
            validate_transition,
        )
        # All 15 goal states + 15 task states from V1.0-2 design §3.2
        assert "draft" in GOAL_TRANSITIONS
        assert "running" in GOAL_TRANSITIONS
        assert "completed" in GOAL_TRANSITIONS
        assert "pending" in TASK_TRANSITIONS
        assert "running" in TASK_TRANSITIONS
        assert "completed_verified" in TASK_TRANSITIONS

    def test_src_runtime_orchestrator_re_exports(self):
        """The orchestrator public surface must be reachable via src.runtime."""
        from src.runtime import (
            execute_goal_pipeline,
            execute_task_step,
            get_runtime_status,
            pause_goal_run,
            resume_goal_run,
            stop_goal_run,
            GoalNotReadyError,
        )
        # All callables
        assert callable(execute_goal_pipeline)
        assert callable(execute_task_step)
        assert callable(get_runtime_status)
        assert callable(pause_goal_run)
        assert callable(resume_goal_run)
        assert callable(stop_goal_run)
        assert GoalNotReadyError is not None


# ---------------------------------------------------------------------------
# (2) Final Summary contract
# ---------------------------------------------------------------------------

def _seed_full_run(db_session):
    """Seed a full 3-station Goal (planner -> coder -> reviewer)."""
    from src.models.agent import AgentStation
    from src.models.model import Model
    from src.models.workspace import Goal, Task

    planner = AgentStation(
        id=str(uuid.uuid4()), name="Planner", role="planner",
        default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
        system_prompt="Plan well.",
    )
    coder = AgentStation(
        id=str(uuid.uuid4()), name="Coder", role="coder",
        default_model_id="model-claude-opus", status="idle", is_enabled=True,
        system_prompt="Write clean code.",
    )
    reviewer = AgentStation(
        id=str(uuid.uuid4()), name="Reviewer", role="reviewer",
        default_model_id="model-claude-3-haiku", status="idle", is_enabled=True,
        system_prompt="Review carefully.",
    )
    db_session.add_all([planner, coder, reviewer])

    for mid, mname in [
        ("model-gpt-4-turbo", "gpt-4-turbo"),
        ("model-claude-opus", "claude-3-opus"),
        ("model-claude-3-haiku", "claude-3-haiku"),
    ]:
        m = Model(id=mid, provider="openai", model_name=mname,
                  display_name=mname, is_enabled=True, max_context_tokens=128000,
                  cost_level=3, speed_level=3)
        m.set_capability_tags(["code", "reasoning"])
        db_session.add(m)
    db_session.commit()

    goal = Goal(id=str(uuid.uuid4()), title="V1.0-4 Final Summary Test",
                status="planning")
    db_session.add(goal)
    db_session.commit()

    tasks = [
        Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Plan",
             description="Plan the work", status="pending",
             assigned_agent_id=planner.id),
        Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Code",
             description="Implement", status="pending",
             assigned_agent_id=coder.id),
        Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Review",
             description="Review code", status="pending",
             assigned_agent_id=reviewer.id),
    ]
    db_session.add_all(tasks)
    db_session.commit()
    return goal, tasks


class TestFinalSummaryContract:
    """Per design §6.3: 'Supervisor 跑一遍 -> Final Summary'."""

    def test_final_summary_present_after_complete_run(self, client: TestClient, db_session):
        goal, _ = _seed_full_run(db_session)

        # Run the Goal to completion
        resp = client.post(f"/api/v1/runtime/execute/{goal.id}")
        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["status"] == "completed"
        assert result["tasks_completed"] == 3

        # The runtime status endpoint must include a non-empty final_summary
        status = client.get(f"/api/v1/runtime/status/{goal.id}").json()["data"]
        assert "final_summary" in status, "final_summary missing from status response"
        summary = status["final_summary"]
        assert isinstance(summary, dict)
        # design §6.3 lists 7 required fields; runtime_service builds:
        #   completed, incomplete, quality, risks, models, handoff_count,
        #   multi_agent, cost
        for required in ("completed", "incomplete", "quality", "risks",
                        "models", "cost"):
            assert required in summary, f"final_summary missing key: {required}"

    def test_final_summary_records_completed_task_titles(self, client: TestClient, db_session):
        goal, _ = _seed_full_run(db_session)
        client.post(f"/api/v1/runtime/execute/{goal.id}")
        status = client.get(f"/api/v1/runtime/status/{goal.id}").json()["data"]
        completed_titles = status["final_summary"]["completed"]
        # All 3 task titles (Plan, Code, Review) should appear
        assert "Plan" in completed_titles
        assert "Code" in completed_titles
        assert "Review" in completed_titles
        assert status["final_summary"]["incomplete"] == []

    def test_final_summary_cost_block_honest_when_no_pricing(self, client: TestClient, db_session):
        """When no provider pricing table is configured, the cost block must
        be honest (not invent currency numbers). Per runtime_service._build_final_summary.
        """
        goal, _ = _seed_full_run(db_session)
        client.post(f"/api/v1/runtime/execute/{goal.id}")
        status = client.get(f"/api/v1/runtime/status/{goal.id}").json()["data"]
        cost = status["final_summary"]["cost"]
        assert cost["available"] is False
        assert cost["currency_estimate"] is None
        assert "note" in cost


# ---------------------------------------------------------------------------
# (3) V1.0 state machine coexists with V1.0-3 Station fields
# ---------------------------------------------------------------------------

class TestV1StationFieldsWithRuntime:
    """The V1.0-3 station fields (slug / is_builtin / handoff_policy) must
    not break the runtime's Task assignment path."""

    def test_builtin_station_runs_through_runtime(self, client: TestClient, db_session):
        """A 6-station default-seeded Goal (already populated by main.py)
        must execute without runtime errors even though the Station rows
        now carry the new V1.0-3 fields.
        """
        from src.models.agent import AgentStation
        from src.models.model import Model
        from src.models.workspace import Goal, Task

        # Manually set up the 6 default stations (as main.py would)
        stations_spec = [
            ("default-planner", "planner", "model-gpt-4-turbo"),
            ("default-coder", "coder", "model-deepseek-coder"),
            ("default-reviewer", "reviewer", "model-gpt-4-turbo"),
            ("default-summarizer", "summarizer", "model-claude-3-haiku"),
            ("default-supervisor", "supervisor", "model-claude-opus"),
        ]
        for sid, role, mid in stations_spec:
            s = AgentStation(
                id=sid, name=role.title(), role=role,
                default_model_id=mid, system_prompt=f"You are a {role}.",
                is_enabled=True, is_builtin=True, slug=role,
                allow_handoff=False, max_steps_per_task=5,
            )
            s.set_handoff_policy({
                "can_initiate": False,
                "on_quota_exhausted": "fallback_backup",
                "on_provider_error": "retry_once",
            })
            db_session.add(s)

        for mid, mname in [
            ("model-gpt-4-turbo", "gpt-4-turbo"),
            ("model-claude-opus", "claude-3-opus"),
            ("model-claude-3-haiku", "claude-3-haiku"),
            ("model-deepseek-coder", "deepseek-coder"),
        ]:
            m = Model(id=mid, provider="openai", model_name=mname,
                      display_name=mname, is_enabled=True, max_context_tokens=128000,
                      cost_level=3, speed_level=3)
            m.set_capability_tags(["code", "reasoning"])
            db_session.add(m)
        db_session.commit()

        # Build a 2-task goal that uses two of the default stations
        goal = Goal(id=str(uuid.uuid4()),
                    title="Default stations e2e",
                    status="planning")
        db_session.add(goal)
        db_session.commit()

        t1 = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Plan",
                  description="Plan", status="pending",
                  assigned_agent_id="default-planner")
        t2 = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Code",
                  description="Code", status="pending",
                  assigned_agent_id="default-coder")
        db_session.add_all([t1, t2])
        db_session.commit()

        resp = client.post(f"/api/v1/runtime/execute/{goal.id}")
        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["status"] == "completed"
        assert result["tasks_completed"] == 2

        # The Status response should reference the Station slugs via the
        # Task -> Station link (no error from the slug column being read).
        status = client.get(f"/api/v1/runtime/status/{goal.id}").json()["data"]
        assert status["completed_tasks"] == 2
        assert status["goal_status"] == "completed"


# ---------------------------------------------------------------------------
# (4) State machine guards illegal transitions
# ---------------------------------------------------------------------------

class TestV1StateMachineGuards:
    """V1.0 design §3.2: '所有状态转换走纯函数矩阵;任何非法转换直接拒绝'
    Runtime must not allow illegal Goal/Task state transitions.
    """

    def test_illegal_goal_transition_rejected(self, db_session):
        from src.runtime import transition_goal, InvalidStateTransition
        from src.models.workspace import Goal

        goal = Goal(id=str(uuid.uuid4()), title="illegal test",
                    status="completed")
        db_session.add(goal)
        db_session.commit()

        # completed -> running is illegal (terminal state)
        with pytest.raises(InvalidStateTransition):
            transition_goal(db_session, goal, "running", summary="test")

    def test_legal_goal_transition_accepted(self, db_session):
        from src.runtime import transition_goal
        from src.models.workspace import Goal

        goal = Goal(id=str(uuid.uuid4()), title="legal test",
                    status="draft")
        db_session.add(goal)
        db_session.commit()

        # draft -> planning is legal
        transition_goal(db_session, goal, "planning", summary="test")
        assert goal.status == "planning"
