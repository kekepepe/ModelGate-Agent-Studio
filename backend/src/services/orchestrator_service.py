"""Capability-first dynamic planning for Agent Runtime v2."""
import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.workspace import Goal, Task


def _agent_for(db: Session, capability: str):
    roles = {"planner": "planner", "research": "research", "code_edit": "coder", "review": "reviewer", "direct": "summarizer"}
    agent = db.query(AgentStation).filter(AgentStation.role == roles[capability], AgentStation.is_enabled == True).order_by(AgentStation.created_at.asc()).first()
    if capability == "direct" and not agent:
        agent = db.query(AgentStation).filter(AgentStation.role == "planner", AgentStation.is_enabled == True).order_by(AgentStation.created_at.asc()).first()
    return agent


def plan_goal(db: Session, goal: Goal) -> List[Task]:
    text = f"{goal.title}\n{goal.description or ''}".lower()
    needs_multi = any(word in text for word in ("协作", "multi-agent", "多 agent", "多agent"))
    parallel_split = needs_multi and any(word in text for word in ("frontend", "front-end", "前端")) and any(word in text for word in ("backend", "back-end", "后端"))
    needs_code = needs_multi or any(word in text for word in ("bug", "fix", "修复", "代码", "api", "test", "pytest", "实现", "file", "文件", "登录", "login"))
    needs_research = any(word in text for word in ("research", "调查", "调研", "资料", "compare", "比较"))
    needs_tests = any(word in text for word in ("test", "pytest", "测试", "验证", "lint", "build"))
    needs_verify = needs_code or needs_tests
    specs: List[Dict] = _preset_specs(goal)
    if specs:
        needs_code = any(spec["capability"] == "code_edit" for spec in specs)
        needs_tests = needs_code
        needs_verify = any(spec["capability"] == "review" for spec in specs)
    else:
        specs = []
    if not specs and needs_research:
        specs.append({"capability": "research", "title": f"Research: {goal.title}", "task_type": "research", "tools": ["workspace_list", "file_read"], "criteria": []})
    if not specs and needs_code:
        # Planning is a graph node only when a Planner capability is actually
        # present. The runtime can still run a single coder task in a lean
        # deployment, while a full Studio makes the plan observable.
        if _agent_for(db, "direct") and db.query(AgentStation).filter(AgentStation.role == "planner", AgentStation.is_enabled == True).first():
            specs.append({"capability": "planner", "title": f"Plan: {goal.title}", "task_type": "planning", "tools": ["workspace_list", "file_read"], "criteria": []})
        criteria = [{"type": "diff_exists"}]
        if needs_tests:
            criteria.append({"type": "tests_pass"})
        code_tools = ["workspace_list", "file_read", "file_search", "file_write", "file_patch", "checkpoint_create", "checkpoint_restore", "terminal_execute", "git_diff"]
        if parallel_split:
            specs.extend([
                {"capability": "code_edit", "title": f"Build frontend: {goal.title}", "task_type": "coding", "tools": code_tools, "criteria": criteria, "parallel_safe": True},
                {"capability": "code_edit", "title": f"Build backend: {goal.title}", "task_type": "coding", "tools": code_tools, "criteria": criteria, "parallel_safe": True},
            ])
        else:
            specs.append({"capability": "code_edit", "title": f"Build: {goal.title}", "task_type": "coding", "tools": code_tools, "criteria": criteria})
    if not specs:
        specs.append({"capability": "direct", "title": f"Answer: {goal.title}", "task_type": "direct", "tools": [], "criteria": []})
    if needs_verify and not any(spec["capability"] == "review" for spec in specs):
        specs.append({"capability": "review", "title": f"Review: {goal.title}", "task_type": "verification", "tools": ["git_diff", "terminal_execute"], "criteria": [{"type": "diff_exists"}] if needs_code else []})

    tasks: List[Task] = []
    dependencies: List[str] = []
    for index, spec in enumerate(specs):
        agent = _agent_for(db, spec["capability"])
        if not agent:
            continue
        task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title=spec["title"], description=goal.description or goal.title,
                    status="pending", assigned_agent_id=agent.id, priority=100 - index * 10,
                    task_type=spec["task_type"], risk_level="medium" if spec["capability"] == "code_edit" else "low")
        task.set_json("required_tools", spec["tools"])
        task.set_json("required_capabilities", [spec["capability"]] + (["parallel_safe"] if spec.get("parallel_safe") else []))
        task.set_json("dependencies", dependencies)
        task.set_json("acceptance_criteria", spec["criteria"])
        db.add(task)
        db.flush()
        tasks.append(task)
        dependencies = [task.id]
    if parallel_split:
        planner = next((task for task in tasks if task.task_type == "planning"), None)
        coding = [task for task in tasks if task.task_type == "coding"]
        reviewer = next((task for task in tasks if task.task_type == "verification"), None)
        if planner and len(coding) == 2:
            for task in coding:
                task.set_json("dependencies", [planner.id])
            if reviewer:
                reviewer.set_json("dependencies", [task.id for task in coding])
    return tasks


def _preset_specs(goal: Goal) -> List[Dict]:
    """Resolve the Studio team card into a real, inspectable task plan."""
    common_plan = {"capability": "planner", "title": f"Plan: {goal.title}", "task_type": "planning", "tools": ["workspace_list", "file_read"], "criteria": []}
    review = {"capability": "review", "title": f"Review: {goal.title}", "task_type": "verification", "tools": ["git_diff", "terminal_execute"], "criteria": []}
    if goal.team_preset == "code-delivery":
        return [
            common_plan,
            {"capability": "code_edit", "title": f"Build: {goal.title}", "task_type": "coding", "tools": ["workspace_list", "file_read", "file_search", "file_write", "file_patch", "checkpoint_create", "checkpoint_restore", "terminal_execute", "git_diff"], "criteria": [{"type": "diff_exists"}, {"type": "tests_pass"}]},
            {**review, "criteria": [{"type": "diff_exists"}]},
        ]
    if goal.team_preset in {"deep-research", "document-production"}:
        delivery_label = "Synthesize" if goal.team_preset == "deep-research" else "Write"
        return [
            common_plan,
            {"capability": "research", "title": f"Research: {goal.title}", "task_type": "research", "tools": ["workspace_list", "file_read", "web_search"], "criteria": []},
            {"capability": "direct", "title": f"{delivery_label}: {goal.title}", "task_type": "direct", "tools": ["file_read"], "criteria": []},
            review,
        ]
    return []


def ready_tasks(db: Session, goal_id: str) -> List[Task]:
    candidates = db.query(Task).filter(Task.goal_id == goal_id, Task.status.in_(["pending", "ready", "assigned"])).all()
    ready = []
    for task in candidates:
        dependencies = task._get_json("dependencies")
        if not dependencies:
            ready.append(task)
            continue
        done = db.query(Task).filter(Task.id.in_(dependencies), Task.status.in_(["completed_verified", "completed_unverified", "completed"])).count()
        if done == len(dependencies):
            ready.append(task)
    return sorted(ready, key=lambda t: (-t.priority, t.created_at))
