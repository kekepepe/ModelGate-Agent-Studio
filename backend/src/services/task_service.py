from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.handoff import WorkerSession
from src.models.model import Model
from src.models.workspace import Task


class TaskNotFoundError(Exception):
    pass


def get_task(db: Session, task_id: str) -> Dict:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise TaskNotFoundError(f"Task '{task_id}' not found")

    data = task.to_dict()

    if task.assigned_agent_id:
        agent = db.query(AgentStation).filter(AgentStation.id == task.assigned_agent_id).first()
        if agent:
            data["agent_name"] = agent.name
            data["agent_role"] = agent.role

    if task.assigned_worker_id:
        worker = db.query(WorkerSession).filter(WorkerSession.id == task.assigned_worker_id).first()
        if worker:
            data["worker_status"] = worker.status
            model = db.query(Model).filter(Model.id == worker.model_id).first() if worker.model_id else None
            data["model_name"] = model.display_name if model else None

    return data
