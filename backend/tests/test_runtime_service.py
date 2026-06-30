import uuid
import pytest
from src.models.agent import AgentStation
from src.models.model import Model
from src.models.workspace import Goal, Task
from src.services import runtime_service


@pytest.fixture
def seed_agents(db_session):
    agents = [
        AgentStation(
            id=str(uuid.uuid4()), name="Planner", role="planner",
            default_model_id="model-gpt-4-turbo", status="idle", is_enabled=True,
            system_prompt="Plan tasks carefully.",
        ),
        AgentStation(
            id=str(uuid.uuid4()), name="Coder", role="coder",
            default_model_id="model-claude-3-opus", status="idle", is_enabled=True,
            system_prompt="Write clean code.",
        ),
        AgentStation(
            id=str(uuid.uuid4()), name="Reviewer", role="reviewer",
            default_model_id="model-claude-3-haiku", status="idle", is_enabled=True,
        ),
    ]
    for a in agents:
        db_session.add(a)
    db_session.commit()
    return agents


@pytest.fixture
def seed_models(db_session):
    models = [
        Model(id="model-gpt-4-turbo", provider="openai", model_name="gpt-4-turbo",
              display_name="GPT-4 Turbo", is_enabled=True, max_context_tokens=128000,
              cost_level=4, speed_level=3),
        Model(id="model-claude-3-opus", provider="anthropic", model_name="claude-3-opus",
              display_name="Claude 3 Opus", is_enabled=True, max_context_tokens=200000,
              cost_level=5, speed_level=3),
        Model(id="model-claude-3-haiku", provider="anthropic", model_name="claude-3-haiku",
              display_name="Claude 3 Haiku", is_enabled=True, max_context_tokens=200000,
              cost_level=1, speed_level=1),
    ]
    for m in models:
        m.set_capability_tags(["code", "reasoning"])
        db_session.add(m)
    db_session.commit()
    return models


class TestExecuteTaskStep:
    def test_execute_task_completes(self, db_session, seed_agents, seed_models):
        goal = Goal(id=str(uuid.uuid4()), title="Test Goal", status="running")
        db_session.add(goal)
        db_session.commit()

        coder = seed_agents[1]
        task = Task(
            id=str(uuid.uuid4()), goal_id=goal.id, title="Build login",
            description="Create login form", status="pending",
            assigned_agent_id=coder.id,
        )
        db_session.add(task)
        db_session.commit()

        result = runtime_service.execute_task_step(db_session, task.id)

        assert result["status"] == "completed"
        assert result["output"] is not None
        assert result["tokens_used"] > 0
        assert result["duration_ms"] > 0
        assert result["model_name"] is not None
        assert result["worker_id"] is not None

        # Verify task state
        db_session.refresh(task)
        assert task.status == "completed"
        assert task.output is not None
        assert task.tokens_used > 0
        assert task.assigned_worker_id is not None

        # Verify agent state
        db_session.refresh(coder)
        assert coder.total_tasks_completed == 1
        assert coder.status == "idle"

        # Verify worker session
        from src.models.handoff import WorkerSession
        worker = db_session.query(WorkerSession).filter(WorkerSession.id == task.assigned_worker_id).first()
        assert worker is not None
        assert worker.status == "completed"
        assert worker.total_tokens_used > 0

        # Verify logs
        from src.models.handoff import ExecutionLog
        logs = db_session.query(ExecutionLog).filter(ExecutionLog.task_id == task.id).all()
        assert len(logs) >= 4

        # Verify quota
        from src.models.quota import QuotaRecord
        quota_count = db_session.query(QuotaRecord).count()
        assert quota_count >= 1

    def test_execute_nonexistent_task_raises(self, db_session):
        with pytest.raises(runtime_service.TaskNotReadyError):
            runtime_service.execute_task_step(db_session, "nonexistent")

    def test_execute_already_completed_task_raises(self, db_session, seed_agents):
        goal = Goal(id=str(uuid.uuid4()), title="G", status="running")
        db_session.add(goal)
        db_session.commit()
        task = Task(
            id=str(uuid.uuid4()), goal_id=goal.id, title="Done", status="completed",
            assigned_agent_id=seed_agents[0].id,
        )
        db_session.add(task)
        db_session.commit()
        with pytest.raises(runtime_service.TaskNotReadyError):
            runtime_service.execute_task_step(db_session, task.id)


class TestExecuteGoalPipeline:
    def test_full_pipeline(self, db_session, seed_agents, seed_models):
        # Create goal + planner task + execution tasks
        goal = Goal(id=str(uuid.uuid4()), title="Build auth system", status="planning")
        db_session.add(goal)
        db_session.commit()

        planner = seed_agents[0]
        coder = seed_agents[1]
        reviewer = seed_agents[2]

        planner_task = Task(
            id=str(uuid.uuid4()), goal_id=goal.id,
            title="Plan auth system", description="Plan the architecture",
            status="pending", assigned_agent_id=planner.id,
        )
        task2 = Task(
            id=str(uuid.uuid4()), goal_id=goal.id,
            title="Build login page", description="Implement the login form",
            status="pending", assigned_agent_id=coder.id,
        )
        task3 = Task(
            id=str(uuid.uuid4()), goal_id=goal.id,
            title="Review implementation", description="Review code quality",
            status="pending", assigned_agent_id=reviewer.id,
        )
        db_session.add_all([planner_task, task2, task3])
        db_session.commit()

        result = runtime_service.execute_goal_pipeline(db_session, goal.id)

        assert result["status"] == "completed"
        assert result["tasks_completed"] == 3
        assert result["tasks_failed"] == 0
        assert result["total_tokens_used"] > 0
        assert result["total_duration_ms"] > 0
        assert len(result["execution_log"]) == 3
        assert result["execution_log"][0]["phase"] == "planning"
        assert result["execution_log"][1]["phase"] == "execution"
        assert result["execution_log"][2]["phase"] == "execution"

    def test_pipeline_wrong_state_raises(self, db_session, seed_agents):
        goal = Goal(id=str(uuid.uuid4()), title="G", status="idle")
        db_session.add(goal)
        db_session.commit()
        with pytest.raises(runtime_service.GoalNotReadyError):
            runtime_service.execute_goal_pipeline(db_session, goal.id)

    def test_pipeline_no_tasks(self, db_session, seed_agents):
        goal = Goal(id=str(uuid.uuid4()), title="G", status="planning")
        db_session.add(goal)
        db_session.commit()
        result = runtime_service.execute_goal_pipeline(db_session, goal.id)
        assert result["status"] == "completed"
        assert result["tasks_completed"] == 0
