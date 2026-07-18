"""Safe, checksum-driven ingestion for Workspace knowledge sources."""

import hashlib
import json
import mimetypes
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.config import settings
from src.models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeSource


ALLOWED_SUFFIXES = {".md", ".txt", ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".sql", ".toml"}
IGNORED_PARTS = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}
MAX_DOCUMENT_BYTES = 1_000_000


class KnowledgeSourceError(ValueError):
    pass


def create_source(db: Session, *, name: str, source_type: str, uri: str, workspace_scope: str = None,
                  sync_policy: str = "manual", metadata: Dict = None) -> Dict:
    _resolve_uri(uri)
    source = KnowledgeSource(
        id=str(uuid.uuid4()), name=name, type=source_type, uri=uri,
        workspace_scope=workspace_scope, sync_policy=sync_policy, status="active",
    )
    source.set_metadata(metadata or {})
    db.add(source)
    db.commit()
    db.refresh(source)
    return source.to_dict()


def list_sources(db: Session) -> List[Dict]:
    return [item.to_dict() for item in db.query(KnowledgeSource).order_by(KnowledgeSource.created_at.desc()).all()]


def list_documents(db: Session, source_id: str) -> List[Dict]:
    _source(db, source_id)
    documents = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.source_id == source_id
    ).order_by(KnowledgeDocument.path.asc()).all()
    document_ids = [item.id for item in documents]
    chunk_counts = dict(
        db.query(KnowledgeChunk.document_id, func.count(KnowledgeChunk.id))
        .filter(KnowledgeChunk.document_id.in_(document_ids))
        .group_by(KnowledgeChunk.document_id)
        .all()
    ) if document_ids else {}
    return [_document_dict(item, chunk_counts.get(item.id, 0)) for item in documents]


def list_chunks(db: Session, document_id: str) -> List[Dict]:
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not document:
        raise KnowledgeSourceError(f"KnowledgeDocument '{document_id}' not found")
    chunks = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.document_id == document_id,
    ).order_by(KnowledgeChunk.chunk_index.asc()).all()
    return [{
        "id": item.id,
        "document_id": item.document_id,
        "chunk_index": item.chunk_index,
        "content": item.content,
        "token_count": item.token_count,
        "symbol_path": item.symbol_path,
        "status": item.status,
        "metadata": item.get_metadata(),
        "created_at": item.created_at.isoformat() if item.created_at else None,
    } for item in chunks]


def set_source_status(db: Session, source_id: str, status: str) -> Dict:
    if status not in {"active", "disabled"}:
        raise KnowledgeSourceError("Source status must be active or disabled")
    source = _source(db, source_id)
    source.status = status
    source.updated_at = datetime.now(timezone.utc)
    db.commit()
    return source.to_dict()


def sync_source(db: Session, source_id: str) -> Dict:
    source = _source(db, source_id)
    if source.status == "disabled":
        raise KnowledgeSourceError("Disabled source cannot be synchronized")
    root = _resolve_uri(source.uri)
    source.status, source.error_message = "syncing", None
    db.flush()
    try:
        files = list(_iter_files(root))
        existing = {
            item.path: item
            for item in db.query(KnowledgeDocument).filter(KnowledgeDocument.source_id == source.id).all()
        }
        seen, added, updated, unchanged = set(), 0, 0, 0
        source_hash = hashlib.sha256()
        for path in files:
            relative = os.path.relpath(path, settings.workspace_root)
            content_bytes = path.read_bytes()
            checksum = hashlib.sha256(content_bytes).hexdigest()
            source_hash.update(relative.encode("utf-8")); source_hash.update(checksum.encode("ascii"))
            seen.add(relative)
            document = existing.get(relative)
            if document and document.checksum == checksum and document.status == "indexed":
                unchanged += 1
                continue
            content = content_bytes.decode("utf-8")
            if not document:
                document = KnowledgeDocument(
                    id=str(uuid.uuid4()), source_id=source.id, path=relative,
                    title=path.name, checksum=checksum,
                    mime_type=mimetypes.guess_type(path.name)[0] or "text/plain",
                )
                db.add(document); db.flush(); added += 1
            else:
                document.title, document.checksum, document.status = path.name, checksum, "indexed"
                document.indexed_at = datetime.now(timezone.utc)
                db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id).delete(synchronize_session=False)
                updated += 1
            chunks = _chunk_text(content)
            db.add_all([
                KnowledgeChunk(
                    id=str(uuid.uuid4()), document_id=document.id, content=chunk,
                    chunk_index=index, token_count=_estimate_tokens(chunk),
                    embedding=json.dumps(_hash_embedding(chunk)),
                    symbol_path=_symbol_path(chunk),
                )
                for index, chunk in enumerate(chunks)
            ])

        deleted = 0
        for relative, document in existing.items():
            if relative in seen or document.status == "deleted":
                continue
            document.status = "deleted"
            db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id).update(
                {"status": "disabled"}, synchronize_session=False,
            )
            deleted += 1
        source.status = "active"
        source.checksum = source_hash.hexdigest()
        source.last_synced_at = datetime.now(timezone.utc)
        source.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"source": source.to_dict(), "added": added, "updated": updated,
                "unchanged": unchanged, "deleted": deleted, "documents": len(files)}
    except Exception as exc:
        db.rollback()
        source = _source(db, source_id)
        source.status, source.error_message = "error", str(exc)
        db.commit()
        raise KnowledgeSourceError(str(exc)) from exc


def _source(db: Session, source_id: str) -> KnowledgeSource:
    source = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
    if not source:
        raise KnowledgeSourceError(f"KnowledgeSource '{source_id}' not found")
    return source


def _resolve_uri(uri: str) -> Path:
    root = os.path.realpath(settings.workspace_root)
    resolved = os.path.realpath(uri if os.path.isabs(uri) else os.path.join(root, uri))
    try:
        in_scope = os.path.commonpath([root, resolved]) == root
    except ValueError:
        in_scope = False
    if not in_scope:
        raise KnowledgeSourceError("Knowledge source must remain inside the configured Workspace Root")
    path = Path(resolved)
    if not path.exists():
        raise KnowledgeSourceError(f"Knowledge source does not exist: {uri}")
    return path


def _iter_files(root: Path) -> Iterable[Path]:
    candidates = [root] if root.is_file() else sorted(root.rglob("*"))
    for path in candidates:
        if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        relative_parts = path.relative_to(root.parent if root.is_file() else root).parts
        if any(part in IGNORED_PARTS or part.startswith(".") for part in relative_parts):
            continue
        if path.stat().st_size > MAX_DOCUMENT_BYTES:
            continue
        yield path


def _chunk_text(content: str, max_chars: int = 1200, overlap: int = 120) -> List[str]:
    normalized = content.replace("\r\n", "\n").strip()
    if not normalized:
        return []
    chunks, start = [], 0
    while start < len(normalized):
        end = min(len(normalized), start + max_chars)
        if end < len(normalized):
            boundary = max(normalized.rfind("\n\n", start, end), normalized.rfind("\n", start, end))
            if boundary > start + max_chars // 2:
                end = boundary
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(start + 1, end - overlap)
    return chunks


def _hash_embedding(text: str, dimensions: int = 64) -> List[float]:
    vector = [0.0] * dimensions
    for token in re.findall(r"[\w.-]+", text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        vector[index] += 1.0 if digest[2] % 2 else -1.0
    norm = sum(value * value for value in vector) ** 0.5 or 1.0
    return [value / norm for value in vector]


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _symbol_path(chunk: str):
    match = re.search(r"^(?:class|def|function|interface|type)\s+([\w$]+)", chunk, re.MULTILINE)
    return match.group(1) if match else None


def _document_dict(document: KnowledgeDocument, chunk_count: int) -> Dict:
    return {"id": document.id, "source_id": document.source_id, "path": document.path,
            "title": document.title, "checksum": document.checksum, "mime_type": document.mime_type,
            "status": document.status, "metadata": document.get_metadata(),
            "chunk_count": chunk_count,
            "indexed_at": document.indexed_at.isoformat() if document.indexed_at else None}
