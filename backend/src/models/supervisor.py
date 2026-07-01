import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, event

from src.core.database import Base


class SupervisorReview(Base):
    __tablename__ = "supervisor_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=False, index=True)
    run_id = Column(String(36), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    summary = Column(Text, nullable=True)
    issues = Column(Text, nullable=False, default="[]")
    suggested_tasks = Column(Text, nullable=False, default="[]")
    passed = Column(Boolean, nullable=False, default=False)
    reviewer_agent_id = Column(String(36), nullable=True)
    reviewer_model_id = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_issues(self) -> List[str]:
        return json.loads(self.issues) if self.issues else []

    def set_issues(self, value: List[str]) -> None:
        self.issues = json.dumps(value, ensure_ascii=False)

    def get_suggested_tasks(self) -> List[Dict[str, str]]:
        return json.loads(self.suggested_tasks) if self.suggested_tasks else []

    def set_suggested_tasks(self, value: List[Dict[str, str]]) -> None:
        self.suggested_tasks = json.dumps(value, ensure_ascii=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "run_id": self.run_id,
            "status": self.status,
            "summary": self.summary,
            "issues": self.get_issues(),
            "suggested_tasks": self.get_suggested_tasks(),
            "passed": self.passed,
            "reviewer_agent_id": self.reviewer_agent_id,
            "reviewer_model_id": self.reviewer_model_id,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@event.listens_for(SupervisorReview, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
