import uuid
import subprocess

from src.models.agent import AgentStation
from src.models.workspace import ExecutionPlan, Goal
from src.models.model import Model
from src.models.workspace import Task
from src.services import runtime_service
from src.services.orchestrator_service import plan_goal, ready_tasks
from src.services.state_machine_service import transition_task


def test_frontend_backend_goal_creates_parallel_isolated_tasks(db_session):
    for name, role in (("planner", "planner"), ("coder-a", "coder"), ("coder-b", "coder"), ("reviewer", "reviewer")):
        db_session.add(AgentStation(id=str(uuid.uuid4()), name=name, role=role, default_model_id=f"{role}-model", is_enabled=True))
    goal = Goal(id=str(uuid.uuid4()), title="前端和后端多Agent协作", description="实现 frontend 和 backend", status="planning")
    db_session.add(goal)
    db_session.commit()

    tasks = plan_goal(db_session, goal)
    planner = next(task for task in tasks if task.task_type == "planning")
    coding = [task for task in tasks if task.task_type == "coding"]
    merge = next(task for task in tasks if task.task_type == "merge")
    verifier = next(task for task in tasks if task.task_type == "verification")
    assert len(coding) == 2
    assert all("parallel_safe" in task._get_json("required_capabilities") for task in coding)
    assert len({task.assigned_agent_id for task in coding}) == 2
    assert all(task._get_json("dependencies") == [planner.id] for task in coding)
    assert set(merge._get_json("dependencies")) == {task.id for task in coding}
    assert verifier._get_json("dependencies") == [merge.id]

    transition_task(db_session, planner, "assigned", summary="Fixture assignment")
    transition_task(db_session, planner, "running", summary="Fixture execution")
    transition_task(db_session, planner, "completed", summary="Fixture completion")
    assert {task.id for task in ready_tasks(db_session, goal.id)} == {task.id for task in coding}


def test_parallel_plan_downgrades_when_only_one_agent_has_capacity(db_session):
    for role in ("planner", "coder", "reviewer"):
        db_session.add(AgentStation(id=str(uuid.uuid4()), name=role, role=role, default_model_id=f"{role}-model", is_enabled=True, max_concurrency=1))
    goal = Goal(id=str(uuid.uuid4()), title="实现 frontend 和 backend", status="planning")
    db_session.add(goal); db_session.commit()

    tasks = plan_goal(db_session, goal)
    plan = db_session.query(ExecutionPlan).filter_by(goal_id=goal.id).one()
    coding = [task for task in tasks if task.task_type == "coding"]
    assert plan.task_mode == "sequential_multi_agent"
    assert "downgraded" in plan.activation_reason
    assert all("parallel_safe" not in task._get_json("required_capabilities") for task in coding)


def test_runtime_executes_parallel_safe_tasks_in_isolated_worktrees(db_session, tmp_path):
    for command in (("init",), ("config", "user.email", "test@example.com"), ("config", "user.name", "Test")):
        subprocess.run(["git", "-C", str(tmp_path), *command], check=True, capture_output=True)
    (tmp_path / "README.md").write_text("base\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "README.md"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "base"], check=True, capture_output=True)
    model = Model(id="parallel-model", provider="mock", model_name="parallel-model", display_name="Parallel", is_enabled=True)
    model.set_capability_tags(["reasoning", "code"])
    agents = [AgentStation(id=str(uuid.uuid4()), name=f"coder-{index}", role="coder", default_model_id=model.id, is_enabled=True) for index in range(2)]
    goal = Goal(id=str(uuid.uuid4()), title="Parallel run", status="planning", execution_mode="mock", workspace_root=str(tmp_path))
    tasks = [Task(id=str(uuid.uuid4()), goal_id=goal.id, title=f"Task {index}", status="pending", assigned_agent_id=agent.id) for index, agent in enumerate(agents)]
    for task in tasks:
        task.set_json("required_capabilities", ["parallel_safe"])
    db_session.add_all([model, *agents, goal, *tasks])
    db_session.commit()

    result = runtime_service.execute_goal_pipeline(db_session, goal.id)
    assert result["tasks_completed"] == 2
    assert {item["phase"] for item in result["execution_log"]} == {"parallel_execution"}
