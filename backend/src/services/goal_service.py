import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.workspace import Goal, Task
from src.core.config import settings


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


def create_goal(db: Session, title: str, description: Optional[str] = None, execution_mode: Optional[str] = None,
                workspace_root: Optional[str] = None, budget_tokens: int = 100000,
                budget_cost_usd: Optional[float] = None, max_duration_seconds: int = 3600,
                team_preset: Optional[str] = None) -> Goal:
    goal = Goal(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        team_preset=team_preset,
        status="idle",
        execution_mode=execution_mode or settings.execution_mode,
        workspace_root=workspace_root or settings.workspace_root,
        budget_tokens=budget_tokens,
        budget_cost_usd=budget_cost_usd,
        max_duration_seconds=max_duration_seconds,
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

    from src.services.orchestrator_service import plan_goal
    tasks = plan_goal(db, goal)
    if not tasks:
        goal.status = "blocked"
        db.commit()
        raise GoalValidationError("No enabled Planner or Agent with a required capability is available")
    db.commit()
    db.refresh(goal)

    return {"goal_id": goal.id, "status": goal.status}
