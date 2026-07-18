import uuid

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.knowledge import SkillDraft
from src.models.workspace import ExecutionPlan, Goal, PlanChange, PlanTask, Task, VerificationResult
from src.schemas.planning import ExecutionPlanContract, PlanTaskContract, ReplanRequest
from src.services import planning_service, replan_service
from src.services.orchestrator_service import _materialize_plan


def _seed_versioned_graph(db_session):
    agents = {}
    for role in ("research", "coder", "reviewer"):
        agent = AgentStation(
            id=str(uuid.uuid4()),
            name=role.title(),
            role=role,
            default_model_id=f"{role}-model",
            is_enabled=True,
        )
        agents[role] = agent
    goal = Goal(
        id=str(uuid.uuid4()),
        title="Versioned repair",
        status="running",
        execution_mode="mock",
    )
    db_session.add_all([goal, *agents.values()])
    db_session.commit()
    contract = ExecutionPlanContract(
        task_mode="sequential_multi_agent",
        goal_summary="Research, implement, verify",
        activation_reason="Three dependent capabilities are required.",
        tasks=[
            PlanTaskContract(
                client_task_id="research",
                objective="Research constraints",
                task_type="research",
                required_capabilities=["research"],
            ),
            PlanTaskContract(
                client_task_id="build",
                objective="Build change",
                task_type="coding",
                required_capabilities=["code_edit"],
                dependencies=["research"],
                acceptance_criteria=[{"type": "diff_exists"}],
            ),
            PlanTaskContract(
                client_task_id="verify",
                objective="Verify change",
                task_type="verification",
                required_capabilities=["review"],
                dependencies=["build"],
            ),
        ],
    )
    plan = planning_service.persist_plan(
        db_session,
        goal,
        contract,
        planner_type="model",
        raw_output=contract.model_dump_json(),
    )
    runtime = _materialize_plan(
        db_session,
        goal,
        plan,
        {"research": agents["research"], "build": agents["coder"], "verify": agents["reviewer"]},
    )
    planning_service.activate_plan(db_session, plan)
    by_title = {task.title: task for task in runtime}
    by_title["Research constraints"].status = "completed_verified"
    by_title["Build change"].status = "completed_unverified"
    by_title["Verify change"].status = "pending"
    db_session.commit()
    return goal, plan, by_title


def test_replan_preserves_valid_tasks_and_replaces_only_invalid_node(client, db_session):
    goal, first_plan, old = _seed_versioned_graph(db_session)
    skill = SkillDraft(id=str(uuid.uuid4()), name="Repair build evidence", scenario="Build evidence failed", status="approved", human_approved=True)
    skill.set_steps(["Inspect failed criterion", "Run the dedicated verifier again"])
    db_session.add_all([
        skill,
        VerificationResult(
            task_id=old["Build change"].id, criterion_type="tests_pass", status="failed",
            command_or_rule="test_runner", evidence="One test failed", exit_code=1,
        ),
    ])
    db_session.commit()
    result = replan_service.request_replan(db_session, goal.id, ReplanRequest(
        trigger="verification_failure",
        reason="Build evidence did not satisfy the completion contract.",
        evidence=[{"criterion": "diff_exists", "status": "failed"}],
        replace_task_ids=[old["Build change"].id],
    ))

    plans = db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal.id).order_by(ExecutionPlan.version).all()
    assert len(plans) == 2
    assert first_plan.status == "superseded"
    assert plans[1].status == "active"
    assert result["decision"]["action"] == "replan_graph"
    assert result["change"]["retained_task_ids"] == ["research", "verify"]
    assert result["change"]["replaced_task_ids"] == ["build"]

    current_plan_tasks = db_session.query(PlanTask).filter(PlanTask.plan_version_id == plans[1].id).all()
    by_client = {task.client_task_id: task for task in current_plan_tasks}
    assert by_client["research"].runtime_task_id == old["Research constraints"].id
    assert by_client["research"].source == "retained"
    assert by_client["verify"].runtime_task_id == old["Verify change"].id
    assert by_client["verify"].source == "retained"
    assert by_client["build"].runtime_task_id != old["Build change"].id
    assert by_client["build"].source == "replaced"

    replacement = db_session.query(Task).filter(Task.id == by_client["build"].runtime_task_id).one()
    db_session.refresh(old["Verify change"])
    assert replacement.parent_task_id == old["Build change"].id
    assert replacement.title == "Revise: Build change"
    assert old["Verify change"]._get_json("dependencies") == [replacement.id]
    assert db_session.query(Task).filter(Task.goal_id == goal.id).count() == 4

    change = db_session.query(PlanChange).filter(PlanChange.to_plan_version_id == plans[1].id).one()
    assert change._get_json("evidence")[0]["trigger"] == "verification_failure"
    replan_context = change._get_json("evidence")[-1]["replan_context"]
    assert replan_context["skills"][0]["id"] == skill.id
    assert replan_context["verification_evidence"][0]["evidence"] == "One test failed"
    assert db_session.query(ExecutionLog).filter(
        ExecutionLog.goal_id == goal.id,
        ExecutionLog.event_type == "plan.updated",
    ).count() == 1

    workspace = client.get(f"/api/v1/workspace/{goal.id}/state").json()["data"]
    assert workspace["active_plan"]["version"] == 2
    assert [item["version"] for item in workspace["plan_versions"]] == [1, 2]
    assert len(workspace["replan_events"]) == 1
    assert any(edge["target"] == old["Verify change"].id for edge in workspace["task_edges"])


def test_explicit_replan_can_remove_and_insert_graph_nodes(client, db_session):
    goal, _, old = _seed_versioned_graph(db_session)
    body = {
        "trigger": "user_change",
        "reason": "Replace verification with a documentation handoff.",
        "plan": {
            "task_mode": "sequential_multi_agent",
            "goal_summary": "Research, implement, document",
            "activation_reason": "User changed the final deliverable.",
            "tasks": [
                {
                    "client_task_id": "research",
                    "objective": "Research constraints",
                    "task_type": "research",
                    "required_capabilities": ["research"],
                },
                {
                    "client_task_id": "build",
                    "objective": "Revise: Build change",
                    "task_type": "coding",
                    "required_capabilities": ["code_edit"],
                    "dependencies": ["research"],
                    "acceptance_criteria": [{"type": "diff_exists"}],
                },
                {
                    "client_task_id": "document",
                    "objective": "Document the verified change",
                    "task_type": "direct",
                    "required_capabilities": ["research"],
                    "dependencies": ["build"],
                },
            ],
        },
    }
    response = client.post(f"/api/v1/goals/{goal.id}/replan", json=body)
    assert response.status_code == 200, response.text
    change = response.json()["data"]["change"]
    assert change["cancelled_task_ids"] == ["verify"]
    assert change["added_task_ids"] == ["document"]
    assert change["replaced_task_ids"] == ["build"]
    db_session.refresh(old["Verify change"])
    assert old["Verify change"].status == "cancelled"


def test_replan_rejects_running_task_without_mutating_plan(client, db_session):
    goal, first_plan, old = _seed_versioned_graph(db_session)
    old["Build change"].status = "running"
    db_session.commit()
    response = client.post(f"/api/v1/goals/{goal.id}/replan", json={
        "trigger": "manual",
        "reason": "Try replacing a live task.",
        "replace_task_ids": [old["Build change"].id],
    })
    assert response.status_code == 409
    assert db_session.query(ExecutionPlan).filter(ExecutionPlan.goal_id == goal.id).count() == 1
    db_session.refresh(first_plan)
    assert first_plan.status == "active"


def test_legacy_parallel_writers_import_with_explicit_worktree_merge_strategy():
    goal = Goal(id=str(uuid.uuid4()), title="Legacy parallel graph", status="running")
    tasks = []
    for title in ("Edit frontend", "Edit backend"):
        task = Task(
            id=str(uuid.uuid4()),
            goal_id=goal.id,
            title=title,
            task_type="coding",
            risk_level="low",
        )
        task.set_json("required_capabilities", ["code_edit", "parallel_safe"])
        task.set_json("acceptance_criteria", [{"type": "diff_exists"}])
        tasks.append(task)

    contract = replan_service._legacy_contract(goal, tasks)

    assert contract.task_mode == "parallel_multi_agent"
    assert [task.merge_strategy for task in contract.tasks] == [
        "legacy_isolated_worktree_patch",
        "legacy_isolated_worktree_patch",
    ]
