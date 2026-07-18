"""Execution-plan orchestration and dependency-aware task readiness."""

import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.workspace import ExecutionPlan, Goal, PlanTask, Task
from src.schemas.planning import ExecutionPlanContract, PlanTaskContract
from src.services import planning_service


def _agent_for(db: Session, capability: str):
    roles = {
        "planning": "planner",
        "planner": "planner",
        "research": "research",
        "code_edit": "coder",
        "code_read": "coder",
        "test": "coder",
        "review": "reviewer",
        "security_review": "reviewer",
        "document_write": "summarizer",
        "direct": "summarizer",
    }
    role = roles.get(capability)
    if not role:
        return None
    agent = (
        db.query(AgentStation)
        .filter(AgentStation.role == role, AgentStation.is_enabled == True)
        .order_by(AgentStation.created_at.asc())
        .first()
    )
    if capability == "direct" and not agent:
        agent = (
            db.query(AgentStation)
            .filter(AgentStation.role == "planner", AgentStation.is_enabled == True)
            .order_by(AgentStation.created_at.asc())
            .first()
        )
    return agent


class RuleBasedPlanningFallback:
    """Compatibility planner used only when a model plan is unavailable."""

    fallback_reason = "No validated model-generated plan was available; rule-based planning fallback was used."

    def build(
        self,
        db: Session,
        goal: Goal,
        fallback_reason: str = None,
    ) -> Tuple[ExecutionPlanContract, Dict[str, AgentStation]]:
        text = f"{goal.title}\n{goal.description or ''}".lower()
        needs_multi = any(word in text for word in ("协作", "multi-agent", "多 agent", "多agent"))
        has_frontend = any(word in text for word in ("frontend", "front-end", "前端", "页面"))
        has_backend = any(word in text for word in ("backend", "back-end", "后端", "接口"))
        parallel_split = (
            has_frontend
            and has_backend
            and any(word in text for word in ("实现", "修改", "build", "implement", "开发"))
        )
        edit_request = any(word in text for word in ("修改", "更新", "替换", "edit", "change", "update"))
        workspace_target = any(word in text for word in ("readme", "文件", "file", ".md", "文案", "一句话"))
        simple_edit = edit_request and workspace_target and not parallel_split
        needs_code = needs_multi or any(
            word in text
            for word in ("bug", "fix", "修复", "代码", "api", "test", "pytest", "实现", "file", "文件", "登录", "login", "修改", "readme")
        )
        needs_research = any(word in text for word in ("research", "调查", "调研", "资料", "材料", "sources", "compare", "比较"))
        needs_tests = any(word in text for word in ("test", "pytest", "测试", "验证", "lint", "build"))
        team_policy = self._team_policy(goal.team_preset)
        specs: List[Dict] = []
        if not specs:
            code_tools = [
                "workspace_list", "file_read", "file_search", "file_write", "file_patch",
                "checkpoint_create", "checkpoint_restore", "terminal_execute", "git_diff",
            ]
            if parallel_split or needs_multi:
                specs.append({
                    "key": "plan",
                    "capability": "planning",
                    "title": f"Plan: {goal.title}",
                    "task_type": "planning",
                    "tools": ["workspace_list", "file_read"],
                    "criteria": [],
                })
            if needs_research:
                specs.append({
                    "key": "research",
                    "capability": "research",
                    "title": f"Research: {goal.title}",
                    "task_type": "research",
                    "tools": ["workspace_list", "file_read"],
                    "criteria": [],
                    "depends_on": ["plan"] if parallel_split or needs_multi else [],
                })
                if not needs_code:
                    specs.append({
                        "key": "synthesize",
                        "capability": "document_write",
                        "title": f"Synthesize: {goal.title}",
                        "task_type": "direct",
                        "tools": ["file_read"],
                        "criteria": [],
                        "depends_on": ["research"],
                    })
            if parallel_split:
                specs.extend([
                    {
                        "key": "frontend",
                        "capability": "code_edit",
                        "title": f"Build frontend: {goal.title}",
                        "task_type": "coding",
                        "tools": code_tools,
                        "criteria": [{"type": "diff_exists"}, *([{"type": "tests_pass"}] if needs_tests else [])],
                        "parallel_safe": True,
                        "workspace_scope": "frontend/**",
                        "depends_on": ["research"] if needs_research else ["plan"],
                    },
                    {
                        "key": "backend",
                        "capability": "code_edit",
                        "title": f"Build backend: {goal.title}",
                        "task_type": "coding",
                        "tools": code_tools,
                        "criteria": [{"type": "diff_exists"}, *([{"type": "tests_pass"}] if needs_tests else [])],
                        "parallel_safe": True,
                        "workspace_scope": "backend/**",
                        "depends_on": ["research"] if needs_research else ["plan"],
                    },
                    {
                        "key": "merge",
                        "capability": "code_edit",
                        "title": f"Merge: {goal.title}",
                        "task_type": "merge",
                        "tools": ["git_diff", "file_patch", "terminal_execute"],
                        "criteria": [{"type": "diff_exists"}],
                        "depends_on": ["frontend", "backend"],
                    },
                ])
            elif needs_code:
                dependencies = ["research"] if needs_research else (["plan"] if needs_multi else [])
                specs.append({
                    "key": "build",
                    "capability": "code_edit",
                    "title": f"Build: {goal.title}",
                    "task_type": "coding",
                    "tools": code_tools,
                    "criteria": [{"type": "diff_exists"}, *([{"type": "tests_pass"}] if needs_tests else [])],
                    "depends_on": dependencies,
                })
            if needs_code and not simple_edit:
                dependency = "merge" if parallel_split else "build"
                specs.append({
                    "key": "verify",
                    "capability": "review",
                    "title": f"Verify: {goal.title}",
                    "task_type": "verification",
                    "tools": ["git_diff", "terminal_execute", *(["test_runner"] if needs_tests else [])],
                    "criteria": [{"type": "diff_exists"}, *([{"type": "tests_pass"}] if needs_tests else [])],
                    "depends_on": [dependency],
                })
            if not specs:
                specs.append({
                    "key": "direct",
                    "capability": "direct",
                    "title": f"Answer: {goal.title}",
                    "task_type": "direct",
                    "tools": [],
                    "criteria": [],
                })

        # A fallback cannot activate unavailable capabilities. Filter them before
        # validating the graph so persisted dependencies always match runtime tasks.
        activated: List[Tuple[Dict, AgentStation]] = []
        for spec in specs:
            agent = _agent_for(db, spec["capability"])
            if agent:
                activated.append((spec, agent))

        client_ids = [f"task-{index + 1}" for index in range(len(activated))]
        client_id_by_key = {
            spec.get("key", f"linear-{index}"): client_id
            for index, ((spec, _), client_id) in enumerate(zip(activated, client_ids))
        }
        plan_tasks: List[PlanTaskContract] = []
        agent_by_client_id: Dict[str, AgentStation] = {}
        for index, ((spec, agent), client_task_id) in enumerate(zip(activated, client_ids)):
            previous_id = client_ids[index - 1] if index else None
            if "depends_on" in spec:
                dependencies = [
                    client_id_by_key[key]
                    for key in spec["depends_on"]
                    if key in client_id_by_key
                ]
            else:
                dependencies = [previous_id] if previous_id else []
            plan_tasks.append(PlanTaskContract(
                client_task_id=client_task_id,
                objective=spec["title"],
                task_type=spec["task_type"],
                required_capabilities=[spec["capability"]],
                required_tools=spec["tools"],
                dependencies=dependencies,
                acceptance_criteria=spec["criteria"],
                risk_level="medium" if spec["capability"] == "code_edit" else "low",
                parallel_safe=bool(spec.get("parallel_safe")),
                workspace_scope=spec.get("workspace_scope"),
                context_query=goal.description or goal.title,
            ))
            agent_by_client_id[client_task_id] = agent

        if not plan_tasks:
            task_mode = "direct"
        elif parallel_split and sum(task.parallel_safe for task in plan_tasks) >= 2:
            task_mode = "parallel_multi_agent"
        elif len(plan_tasks) == 1 and plan_tasks[0].task_type == "direct":
            task_mode = "direct"
        elif len(plan_tasks) == 1:
            task_mode = "single_agent"
        else:
            task_mode = "sequential_multi_agent"

        activation_reason = self._activation_reason(task_mode, len(plan_tasks))
        if team_policy:
            activation_reason += f" Team policy '{goal.team_preset}' supplied a capability pool; it did not force a role sequence."
        contract = ExecutionPlanContract(
            task_mode=task_mode,
            goal_summary=goal.description or goal.title,
            assumptions=["Capability availability was resolved from enabled Agent stations."],
            required_context=[goal.workspace_root] if goal.workspace_root else [],
            activation_reason=activation_reason,
            tasks=plan_tasks,
            final_acceptance_criteria=[],
            estimated_cost={"team_policy": team_policy},
            fallback_reason=fallback_reason or self.fallback_reason,
        )
        return contract, agent_by_client_id

    @staticmethod
    def _activation_reason(task_mode: str, task_count: int) -> str:
        reasons = {
            "direct": "The Goal can be answered directly without activating a redundant team.",
            "single_agent": "One enabled capability can complete the Goal without coordination overhead.",
            "sequential_multi_agent": "The Goal requires dependent capabilities that must run in sequence.",
            "parallel_multi_agent": "The Goal contains isolated frontend and backend work that can run in parallel.",
        }
        return f"{reasons[task_mode]} Activated tasks: {task_count}."

    @staticmethod
    def _team_policy(team_preset: Optional[str]) -> Dict:
        policies = {
            "code-delivery": {
                "capabilities": ["planning", "code_read", "code_edit", "test", "review"],
                "prefer_single_agent": True, "max_parallel": 2,
                "independent_review": "high_risk", "isolate_parallel_writes": True,
            },
            "deep-research": {
                "capabilities": ["planning", "research", "data_analysis", "document_write", "review"],
                "prefer_single_agent": True, "max_parallel": 3,
                "independent_review": "on_demand", "isolate_parallel_writes": True,
            },
            "document-production": {
                "capabilities": ["planning", "research", "document_write", "review"],
                "prefer_single_agent": True, "max_parallel": 2,
                "independent_review": "on_demand", "isolate_parallel_writes": True,
            },
            "custom-team": {
                "capabilities": [], "prefer_single_agent": True, "max_parallel": 3,
                "independent_review": "high_risk", "isolate_parallel_writes": True,
            },
        }
        return policies.get(team_preset, {})


def plan_goal(db: Session, goal: Goal) -> List[Task]:
    """Prefer a model-generated contract and visibly fall back when unavailable."""
    from src.services.model_orchestrator_service import (
        ModelOrchestrator,
        ModelPlanningFailed,
        ModelPlanningUnavailable,
    )

    planner_type = "model"
    raw_output = None
    repair_records = []
    try:
        result = ModelOrchestrator().plan(db, goal)
        if not result.contract.tasks:
            empty_plan_error = ModelPlanningFailed(
                "Model returned a direct plan without an executable response task"
            )
            empty_plan_error.raw_output = result.raw_output
            empty_plan_error.repair_records = result.repair_records
            raise empty_plan_error
        contract = result.contract
        agents = result.agents
        raw_output = result.raw_output
        repair_records = result.repair_records
    except (ModelPlanningUnavailable, ModelPlanningFailed) as exc:
        planner_type = "rule_fallback"
        raw_output = getattr(exc, "raw_output", None)
        repair_records = getattr(exc, "repair_records", [])
        contract, agents = RuleBasedPlanningFallback().build(
            db,
            goal,
            fallback_reason=f"{type(exc).__name__}: {exc}",
        )
    if not contract.tasks:
        return []
    plan = planning_service.persist_plan(
        db,
        goal,
        contract,
        planner_type=planner_type,
        raw_output=raw_output or contract.model_dump_json(),
        repair_records=repair_records,
    )
    tasks = _materialize_plan(db, goal, plan, agents)
    planning_service.activate_plan(db, plan, confirmed=False)
    return tasks


def _materialize_plan(
    db: Session,
    goal: Goal,
    plan: ExecutionPlan,
    agents: Dict[str, AgentStation],
    *,
    retained_runtime_by_client_id: Optional[Dict[str, Task]] = None,
    replacement_parent_by_client_id: Optional[Dict[str, str]] = None,
    source_by_client_id: Optional[Dict[str, str]] = None,
    commit: bool = True,
) -> List[Task]:
    plan_tasks = (
        db.query(PlanTask)
        .filter(PlanTask.plan_version_id == plan.id)
        .order_by(PlanTask.created_at.asc())
        .all()
    )
    retained_runtime_by_client_id = retained_runtime_by_client_id or {}
    replacement_parent_by_client_id = replacement_parent_by_client_id or {}
    source_by_client_id = source_by_client_id or {}
    runtime_tasks: List[Task] = []
    runtime_id_by_client_id: Dict[str, str] = {}
    runtime_task_by_client_id: Dict[str, Task] = {}
    reserved_parallel_loads: Dict[str, int] = {}
    parallel_capacity_downgraded = False
    for index, plan_task in enumerate(plan_tasks):
        retained = retained_runtime_by_client_id.get(plan_task.client_task_id)
        if retained:
            plan_task.runtime_task_id = retained.id
            plan_task.source = source_by_client_id.get(plan_task.client_task_id, "retained")
            retained.plan_version_id = plan.id
            retained.plan_task_id = plan_task.id
            retained.plan_source = plan.planner_type
            runtime_id_by_client_id[plan_task.client_task_id] = retained.id
            runtime_task_by_client_id[plan_task.client_task_id] = retained
            continue
        from src.services import agent_selector_service
        selection_args = {
            "goal_id": goal.id, "task_id": plan_task.id, "task_type": plan_task.task_type,
            "required_capabilities": plan_task._get_json("required_capabilities"),
            "required_tools": plan_task._get_json("required_tools"), "risk_level": plan_task.risk_level,
            "workspace_scope": plan_task.workspace_scope, "require_model": False, "persist": True,
        }
        try:
            selection = agent_selector_service.select_agent(
                db, **selection_args,
                reserved_loads=reserved_parallel_loads if plan_task.parallel_safe else None,
            )
        except agent_selector_service.NoEligibleAgentError:
            if not plan_task.parallel_safe:
                raise
            selection = agent_selector_service.select_agent(db, **selection_args)
            parallel_capacity_downgraded = True
        agent = db.query(AgentStation).filter(AgentStation.id == selection["selected_agent_id"]).one()
        if plan_task.parallel_safe:
            reserved_parallel_loads[agent.id] = reserved_parallel_loads.get(agent.id, 0) + 1
        runtime_task = Task(
            id=str(uuid.uuid4()),
            goal_id=goal.id,
            title=plan_task.objective,
            description=goal.description or goal.title,
            status="waiting_approval" if plan_task.approval_required else "pending",
            assigned_agent_id=agent.id,
            priority=100 - index * 10,
            task_type=plan_task.task_type,
            risk_level=plan_task.risk_level,
            plan_version_id=plan.id,
            plan_task_id=plan_task.id,
            plan_source=plan.planner_type,
            parent_task_id=replacement_parent_by_client_id.get(plan_task.client_task_id),
        )
        runtime_task.set_json("required_tools", plan_task._get_json("required_tools"))
        runtime_task.set_json("required_capabilities", plan_task._get_json("required_capabilities") + (["parallel_safe"] if plan_task.parallel_safe else []))
        runtime_task.set_json("dependencies", [])
        runtime_task.set_json("acceptance_criteria", plan_task._get_json("acceptance_criteria"))
        db.add(runtime_task)
        db.flush()
        plan_task.runtime_task_id = runtime_task.id
        plan_task.source = source_by_client_id.get(plan_task.client_task_id, "created")
        runtime_id_by_client_id[plan_task.client_task_id] = runtime_task.id
        runtime_task_by_client_id[plan_task.client_task_id] = runtime_task
        runtime_tasks.append(runtime_task)

    for plan_task in plan_tasks:
        runtime_task = runtime_task_by_client_id.get(plan_task.client_task_id)
        if not runtime_task:
            continue
        if runtime_task.status not in {"completed", "completed_verified", "completed_unverified", "skipped"}:
            runtime_task.set_json(
                "dependencies",
                [runtime_id_by_client_id[item] for item in plan_task._get_json("dependencies") if item in runtime_id_by_client_id],
            )
    if parallel_capacity_downgraded:
        plan.task_mode = "sequential_multi_agent"
        plan.activation_reason += " Parallel execution was downgraded because available Agent concurrency could not safely cover every branch."
        for plan_task in plan_tasks:
            if not plan_task.parallel_safe:
                continue
            plan_task.parallel_safe = False
            runtime_task = runtime_task_by_client_id.get(plan_task.client_task_id)
            if runtime_task:
                runtime_task.set_json("required_capabilities", [
                    item for item in runtime_task._get_json("required_capabilities") if item != "parallel_safe"
                ])
    if commit:
        db.commit()
    else:
        db.flush()
    return runtime_tasks


def ready_tasks(db: Session, goal_id: str) -> List[Task]:
    candidates = db.query(Task).filter(
        Task.goal_id == goal_id,
        Task.status.in_(["pending", "ready", "assigned"]),
    ).all()
    ready = []
    for task in candidates:
        dependencies = task._get_json("dependencies")
        if not dependencies:
            ready.append(task)
            continue
        dependency_rows = db.query(Task).filter(Task.id.in_(dependencies)).all()
        if len(dependency_rows) != len(set(dependencies)):
            task.blocked_reason = "Task graph contains a missing dependency"
            continue
        if all(item.status in {"completed_verified", "completed_unverified", "completed", "skipped"} for item in dependency_rows):
            ready.append(task)
    db.commit()
    return sorted(ready, key=lambda task: (-task.priority, task.created_at))
