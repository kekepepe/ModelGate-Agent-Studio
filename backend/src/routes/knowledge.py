from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.knowledge import ApprovalRequest, KnowledgeSourceCreate, PreferenceCreate, RetrievalRequest, SourceStatusRequest
import json

from src.models.knowledge import SkillDraft
from src.models.handoff import WorkerSession
from src.models.workspace import Goal
from src.services import curator_service, knowledge_source_service, memory_vector_service, retrieval_service

router = APIRouter(tags=["knowledge"])


def _success(data, status_code=200):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail={"success": False, "error": {"code": code, "message": message}})


@router.post("/knowledge/generate/{goal_id}")
def generate_memories(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = curator_service.generate_memories(db, goal_id)
        return _success(result)
    except Exception as e:
        raise _error("INTERNAL_ERROR", str(e), 500)


@router.get("/knowledge/evolution")
def get_evolution_summary(goal_id: Optional[str] = Query(None), run_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    try:
        if run_id and not goal_id:
            goal = db.query(Goal).filter(Goal.run_id == run_id).first()
            goal_id = goal.id if goal else "__missing_run__"
        return _success(curator_service.get_evolution_summary(db, goal_id))
    except Exception as e:
        raise _error("INTERNAL_ERROR", str(e), 500)


@router.post("/knowledge/memories/{memory_id}/approve")
def approve_memory(memory_id: str, req: ApprovalRequest, db: Session = Depends(get_db)):
    try:
        result = curator_service.approve_memory(db, memory_id, req.approved, req.approved_by)
        return _success(result)
    except ValueError as e:
        raise _error("NOT_FOUND", str(e), 404)
    except Exception as e:
        raise _error("INTERNAL_ERROR", str(e), 500)


@router.post("/knowledge/skills/{skill_id}/approve")
def approve_skill(skill_id: str, req: ApprovalRequest, db: Session = Depends(get_db)):
    try:
        result = curator_service.approve_skill(db, skill_id, req.approved, req.approved_by)
        return _success(result)
    except ValueError as e:
        raise _error("NOT_FOUND", str(e), 404)
    except Exception as e:
        raise _error("INTERNAL_ERROR", str(e), 500)


@router.post("/knowledge/sources", status_code=201)
def create_source(req: KnowledgeSourceCreate, db: Session = Depends(get_db)):
    try:
        return _success(knowledge_source_service.create_source(
            db, name=req.name, source_type=req.type, uri=req.uri,
            workspace_scope=req.workspace_scope, sync_policy=req.sync_policy,
            metadata=req.metadata,
        ), 201)
    except knowledge_source_service.KnowledgeSourceError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.get("/knowledge/sources")
def list_sources(db: Session = Depends(get_db)):
    return _success(knowledge_source_service.list_sources(db))


@router.post("/knowledge/sources/{source_id}/sync")
def sync_source(source_id: str, db: Session = Depends(get_db)):
    try:
        return _success(knowledge_source_service.sync_source(db, source_id))
    except knowledge_source_service.KnowledgeSourceError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.get("/knowledge/sources/{source_id}/documents")
def list_source_documents(source_id: str, db: Session = Depends(get_db)):
    try:
        return _success(knowledge_source_service.list_documents(db, source_id))
    except knowledge_source_service.KnowledgeSourceError as exc:
        raise _error("NOT_FOUND", str(exc), 404)


@router.get("/knowledge/documents/{document_id}/chunks")
def list_document_chunks(document_id: str, db: Session = Depends(get_db)):
    try:
        return _success(knowledge_source_service.list_chunks(db, document_id))
    except knowledge_source_service.KnowledgeSourceError as exc:
        raise _error("NOT_FOUND", str(exc), 404)


@router.patch("/knowledge/sources/{source_id}/status")
def update_source_status(source_id: str, req: SourceStatusRequest, db: Session = Depends(get_db)):
    try:
        return _success(knowledge_source_service.set_source_status(db, source_id, req.status))
    except knowledge_source_service.KnowledgeSourceError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.post("/knowledge/preferences", status_code=201)
def create_preference(req: PreferenceCreate, db: Session = Depends(get_db)):
    try:
        return _success(curator_service.create_user_preference(
            db, req.title, req.content, created_by=req.created_by, tags=req.tags,
        ), 201)
    except ValueError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.get("/knowledge/memories/search")
def search_memories(
    q: str = Query(..., min_length=1, max_length=4000),
    type: Optional[str] = Query(None),
    approved: Optional[bool] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return _success(memory_vector_service.search_memories(
        db, q, memory_type=type, require_approved=approved, limit=limit,
    ))


@router.get("/knowledge/skills/{skill_id}")
def get_skill_detail(skill_id: str, db: Session = Depends(get_db)):
    skill = db.query(SkillDraft).filter(SkillDraft.id == skill_id).first()
    if not skill:
        raise _error("NOT_FOUND", f"Skill '{skill_id}' not found", 404)
    detail = skill.to_dict()
    detail["success_rate"] = skill.success_rate
    return _success(detail)


class ConflictResolveRequest(BaseModel):
    keep: str = Field("stored", pattern="^(stored|incoming|merge)$")


@router.post("/knowledge/memories/{memory_id}/resolve")
def resolve_memory_conflict(memory_id: str, req: ConflictResolveRequest, db: Session = Depends(get_db)):
    try:
        return _success(curator_service.resolve_memory_conflict(db, memory_id, req.keep))
    except ValueError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.post("/context/retrieve")
def retrieve_context(req: RetrievalRequest, db: Session = Depends(get_db)):
    try:
        payload = req.model_dump()
        source_types = payload.pop("source_types") or ["knowledge"]
        unknown = set(source_types) - {"memory", "skill", "knowledge"}
        if unknown:
            raise _error("BAD_REQUEST", f"Unknown source_types: {sorted(unknown)}", 400)
        if set(source_types) == {"knowledge"}:
            # Legacy contract: chunks-only retrieval, unchanged response shape.
            return _success(retrieval_service.retrieve(db, **payload))
        result: dict = {"policy": "unified_memory_skill_knowledge_v1", "source_types": source_types, "query": req.query}
        if "memory" in source_types:
            result["memories"] = memory_vector_service.search_memories(db, req.query, limit=req.limit)
        if "skill" in source_types:
            result["skills"] = memory_vector_service.search_skills(db, req.query, limit=req.limit)
        if "knowledge" in source_types:
            result["knowledge"] = retrieval_service.retrieve(db, **payload)
        return _success(result)
    except ValueError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.get("/goals/{goal_id}/context-runs")
def list_context_runs(goal_id: str, db: Session = Depends(get_db)):
    return _success(retrieval_service.get_runs(db, goal_id))


@router.get("/tasks/{task_id}/context-snapshots")
def list_task_context_snapshots(task_id: str, db: Session = Depends(get_db)):
    """V1.5 QL8: 'which past knowledge did this task use' — redacted snapshot
    payloads with memory/preference/skill citation summaries."""
    from src.models.knowledge import ContextPackageSnapshot

    snapshots = (
        db.query(ContextPackageSnapshot)
        .filter(ContextPackageSnapshot.worker_id.in_(
            db.query(WorkerSession.id).filter(WorkerSession.task_id == task_id)
        ))
        .order_by(ContextPackageSnapshot.created_at.desc())
        .limit(10)
        .all()
    )
    items = []
    for snapshot in snapshots:
        try:
            payload = json.loads(snapshot.payload)
        except (json.JSONDecodeError, TypeError):
            continue
        items.append({
            "id": snapshot.id,
            "worker_id": snapshot.worker_id,
            "token_count": snapshot.token_count,
            "checksum": snapshot.checksum,
            "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
            "project_memories": [
                {"id": m.get("id"), "title": m.get("title"), "confidence": m.get("confidence")}
                for m in payload.get("project_memories") or []
            ],
            "user_preferences": [
                {"id": m.get("id"), "title": m.get("title")}
                for m in payload.get("user_preferences") or []
            ],
            "skills": [
                {"id": s.get("id"), "name": s.get("name"), "success_rate": s.get("success_rate")}
                for s in payload.get("skills") or []
            ],
            "citations": payload.get("citations") or [],
            "policy": payload.get("policy"),
        })
    return _success({"items": items, "total": len(items)})
