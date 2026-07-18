from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.knowledge import ApprovalRequest, KnowledgeSourceCreate, RetrievalRequest, SourceStatusRequest
from src.models.workspace import Goal
from src.services import curator_service, knowledge_source_service, retrieval_service

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


@router.post("/context/retrieve")
def retrieve_context(req: RetrievalRequest, db: Session = Depends(get_db)):
    try:
        return _success(retrieval_service.retrieve(db, **req.model_dump()))
    except ValueError as exc:
        raise _error("BAD_REQUEST", str(exc), 400)


@router.get("/goals/{goal_id}/context-runs")
def list_context_runs(goal_id: str, db: Session = Depends(get_db)):
    return _success(retrieval_service.get_runs(db, goal_id))
