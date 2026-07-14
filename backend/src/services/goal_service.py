import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.workspace import Goal, Task


class GoalNotFoundError(Exception):
    pass


class GoalValidationError(Exception):
    pass


# The MVP has a deliberately explicit serial plan. It gives a newly created
# Goal a truthful, inspectable collaboration flow without pretending that the
# Runtime already supports arbitrary DAG scheduling.
DEFAULT_GOAL_PLAN = (
    ("planner", "Plan", "明确交付物、约束和执行顺序", 30),
    ("coder", "Build", "实现主要方案或产出", 20),
    ("reviewer", "Review", "审查质量、遗漏和风险", 10),
)


def create_goal(db: Session, title: str, description: Optional[str] = None) -> Goal:
    goal = Goal(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        status="idle",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goal(db: Session, goal_id: str) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise GoalNotFoundError(f"Goal '{goal_id}' not found")
    return goal


def start_goal(db: Session, goal_id: str) -> Dict[str, str]:
    goal = get_goal(db, goal_id)
    if goal.status != "idle":
        raise GoalValidationError(f"Goal must be idle to start, current status: {goal.status}")

    goal.status = "planning"
    goal.updated_at = datetime.now(timezone.utc)

    enabled_agents = (
        db.query(AgentStation)
        .filter(AgentStation.is_enabled == True)
        .order_by(AgentStation.created_at.asc(), AgentStation.id.asc())
        .all()
    )
    agents_by_role = {}
    for agent in enabled_agents:
        agents_by_role.setdefault(agent.role, agent)

    planner = agents_by_role.get("planner")
    if not planner:
        raise GoalValidationError("No enabled Planner Agent is available; configure an Agent Station before starting a Goal")

    goal_context = goal.description or goal.title
    for role, action, instruction, priority in DEFAULT_GOAL_PLAN:
        agent = agents_by_role.get(role)
        # Planner is required above; optional roles keep minimal deployments
        # executable while a fully seeded install receives the three-step flow.
        if not agent:
            continue
        task = Task(
            id=str(uuid.uuid4()),
            goal_id=goal.id,
            title=f"{action}: {goal.title}",
            description=f"{instruction}。Goal: {goal_context}",
            status="pending",
            assigned_agent_id=agent.id,
            priority=priority,
        )
        db.add(task)
    db.commit()
    db.refresh(goal)

    return {"goal_id": goal.id, "status": goal.status}
