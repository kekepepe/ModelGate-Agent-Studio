from typing import Dict, List

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import WorkerSession
from src.models.model import Model
from src.models.workspace import Goal, Task


class WorkspaceNotFoundError(Exception):
    pass


def get_workspace_state(db: Session, goal_id: str) -> Dict:
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise WorkspaceNotFoundError(f"Goal '{goal_id}' not found")

    tasks = db.query(Task).filter(Task.goal_id == goal_id).all()

    # All registered agents
    agents = db.query(AgentStation).filter(AgentStation.is_enabled == True).all()

    # Workers related to this goal
    workers = db.query(WorkerSession).filter(WorkerSession.goal_id == goal_id).all()

    model_ids = {w.model_id for w in workers if w.model_id}
    models = {}
    if model_ids:
        db_models = db.query(Model).filter(Model.id.in_(model_ids)).all()
        models = {m.id: m.display_name for m in db_models}

    return {
        "goal": goal.to_dict() if goal else None,
        "tasks": [t.to_dict() for t in tasks],
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role,
                "status": a.status,
                "default_model_id": a.default_model_id,
                "is_enabled": a.is_enabled,
            }
            for a in agents
        ],
        "workers": [
            {
                "id": w.id,
                "agent_id": w.agent_id,
                "model_id": w.model_id,
                "goal_id": w.goal_id,
                "task_id": w.task_id,
                "inherited_from_handoff_id": w.inherited_from_handoff_id,
                "status": w.status,
                "total_tokens_used": w.total_tokens_used,
                "model_name": models.get(w.model_id) if w.model_id else None,
            }
            for w in workers
        ],
    }
