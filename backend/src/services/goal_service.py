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

    # MVP: Create 1 initial Task assigned to the first available Planner Agent
    planner = db.query(AgentStation).filter(
        AgentStation.role == "planner",
        AgentStation.is_enabled == True,
    ).first()

    task = Task(
        id=str(uuid.uuid4()),
        goal_id=goal.id,
        title=f"Plan: {goal.title}",
        description=f"Planner Agent 拆解任务：{goal.title}",
        status="pending",
        assigned_agent_id=planner.id if planner else None,
    )
    db.add(task)
    db.commit()
    db.refresh(goal)

    return {"goal_id": goal.id, "status": goal.status}
