import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, UniqueConstraint, event

from src.core.database import Base


class MemoryDraft(Base):
    __tablename__ = "memory_drafts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_run_id = Column(String(36), nullable=True)
    source_goal_id = Column(String(36), nullable=True, index=True)
    type = Column(String(50), nullable=False, default="project_memory", index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=0.5)
    reason = Column(Text, nullable=True)
    tags = Column(Text, nullable=False, default="[]")
    human_approved = Column(Boolean, nullable=True, index=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    extra_metadata = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_tags(self) -> List[str]:
        return json.loads(self.tags) if self.tags else []
    def set_tags(self, v: List[str]) -> None:
        self.tags = json.dumps(v, ensure_ascii=False)
    def get_metadata(self) -> Dict[str, Any]:
        return json.loads(self.extra_metadata) if self.extra_metadata else {}
    def set_metadata(self, v: Dict[str, Any]) -> None:
        self.extra_metadata = json.dumps(v, ensure_ascii=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "source_run_id": self.source_run_id,
            "source_goal_id": self.source_goal_id, "type": self.type,
            "title": self.title, "content": self.content, "confidence": self.confidence,
            "reason": self.reason, "tags": self.get_tags(),
            "human_approved": self.human_approved, "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "metadata": self.get_metadata(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SkillDraft(Base):
    __tablename__ = "skill_drafts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_run_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, default="1.0")
    scenario = Column(Text, nullable=True)
    input_requirements = Column(Text, nullable=True)
    steps = Column(Text, nullable=False, default="[]")
    recommended_agents = Column(Text, nullable=False, default="[]")
    recommended_models = Column(Text, nullable=False, default="[]")
    tools = Column(Text, nullable=False, default="[]")
    output_format = Column(Text, nullable=True)
    success_criteria = Column(Text, nullable=True)
    common_failures = Column(Text, nullable=False, default="[]")
    status = Column(String(50), nullable=False, default="draft", index=True)
    human_approved = Column(Boolean, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_steps(self) -> List[str]: return json.loads(self.steps) if self.steps else []
    def set_steps(self, v: List[str]) -> None: self.steps = json.dumps(v, ensure_ascii=False)
    def get_agents(self) -> List[str]: return json.loads(self.recommended_agents) if self.recommended_agents else []
    def set_agents(self, v: List[str]) -> None: self.recommended_agents = json.dumps(v, ensure_ascii=False)
    def get_models(self) -> List[str]: return json.loads(self.recommended_models) if self.recommended_models else []
    def set_models(self, v: List[str]) -> None: self.recommended_models = json.dumps(v, ensure_ascii=False)
    def get_tools(self) -> List[str]: return json.loads(self.tools) if self.tools else []
    def set_tools(self, v: List[str]) -> None: self.tools = json.dumps(v, ensure_ascii=False)
    def get_failures(self) -> List[str]: return json.loads(self.common_failures) if self.common_failures else []
    def set_failures(self, v: List[str]) -> None: self.common_failures = json.dumps(v, ensure_ascii=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "source_run_id": self.source_run_id,
            "name": self.name, "scenario": self.scenario,
            "version": self.version,
            "input_requirements": self.input_requirements,
            "steps": self.get_steps(), "recommended_agents": self.get_agents(),
            "recommended_models": self.get_models(), "tools": self.get_tools(),
            "output_format": self.output_format, "success_criteria": self.success_criteria,
            "common_failures": self.get_failures(),
            "status": self.status, "human_approved": self.human_approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "success_count": self.success_count, "failure_count": self.failure_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@event.listens_for(MemoryDraft, "before_update")
@event.listens_for(SkillDraft, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    uri = Column(Text, nullable=False)
    workspace_scope = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="active", index=True)
    sync_policy = Column(String(30), nullable=False, default="manual")
    checksum = Column(String(128), nullable=True)
    extra_metadata = Column(Text, nullable=False, default="{}")
    last_synced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def get_metadata(self): return json.loads(self.extra_metadata or "{}")
    def set_metadata(self, value): self.extra_metadata = json.dumps(value, ensure_ascii=False)
    def to_dict(self):
        return {"id": self.id, "name": self.name, "type": self.type, "uri": self.uri,
                "workspace_scope": self.workspace_scope, "status": self.status,
                "sync_policy": self.sync_policy, "checksum": self.checksum,
                "metadata": self.get_metadata(), "error_message": self.error_message,
                "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None}


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (UniqueConstraint("source_id", "path", name="uq_knowledge_document_source_path"),)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), nullable=False, index=True)
    path = Column(Text, nullable=False)
    title = Column(String(500), nullable=False)
    checksum = Column(String(128), nullable=False, index=True)
    mime_type = Column(String(100), nullable=True)
    extra_metadata = Column(Text, nullable=False, default="{}")
    status = Column(String(30), nullable=False, default="indexed", index=True)
    indexed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    def get_metadata(self): return json.loads(self.extra_metadata or "{}")
    def set_metadata(self, value): self.extra_metadata = json.dumps(value, ensure_ascii=False)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunk_document_index"),)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    embedding = Column(Text, nullable=True)
    symbol_path = Column(Text, nullable=True)
    extra_metadata = Column(Text, nullable=False, default="{}")
    status = Column(String(30), nullable=False, default="active", index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    def get_metadata(self): return json.loads(self.extra_metadata or "{}")
    def set_metadata(self, value): self.extra_metadata = json.dumps(value, ensure_ascii=False)


class RetrievalRun(Base):
    __tablename__ = "retrieval_runs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String(36), nullable=True, index=True)
    task_id = Column(String(36), nullable=True, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    query = Column(Text, nullable=False)
    policy = Column(String(100), nullable=False, index=True)
    filters = Column(Text, nullable=False, default="{}")
    latency_ms = Column(Integer, nullable=False, default=0)
    token_budget = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="completed", index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    def get_filters(self): return json.loads(self.filters or "{}")
    def set_filters(self, value): self.filters = json.dumps(value, ensure_ascii=False)


class RetrievedContextItem(Base):
    __tablename__ = "retrieved_context_items"
    __table_args__ = (UniqueConstraint("retrieval_run_id", "rank", name="uq_retrieved_item_run_rank"),)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    retrieval_run_id = Column(String(36), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, index=True)
    source_id = Column(String(36), nullable=False, index=True)
    chunk_id = Column(String(36), nullable=True, index=True)
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    used = Column(Boolean, nullable=False, default=False, index=True)
    citation = Column(Text, nullable=True)
    token_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class ContextPackageSnapshot(Base):
    __tablename__ = "context_package_snapshots"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    worker_id = Column(String(36), nullable=False, index=True)
    plan_version_id = Column(String(36), nullable=True, index=True)
    retrieval_run_id = Column(String(36), nullable=True, index=True)
    payload = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    checksum = Column(String(128), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
