from src.core.config import settings
from src.models.knowledge import ContextPackageSnapshot, KnowledgeChunk, KnowledgeDocument, RetrievalRun, RetrievedContextItem
from src.models.workspace import Goal, Task
from src.services.context_service import build_context_package, persist_context_snapshot


def _create_and_sync(client, root, monkeypatch):
    monkeypatch.setattr(settings, "workspace_root", str(root))
    response = client.post("/api/v1/knowledge/sources", json={
        "name": "Docs", "type": "workspace", "uri": "docs", "workspace_scope": "docs/**",
    })
    assert response.status_code == 201, response.text
    source_id = response.json()["data"]["id"]
    synced = client.post(f"/api/v1/knowledge/sources/{source_id}/sync")
    assert synced.status_code == 200, synced.text
    return source_id, synced.json()["data"]


def test_checksum_sync_is_incremental_and_soft_disables_deleted_documents(client, db_session, tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    architecture = docs / "architecture.md"
    architecture.write_text("# Runtime\n\nPlan versions are immutable.\n", encoding="utf-8")
    (docs / ".hidden.md").write_text("secret", encoding="utf-8")
    source_id, first = _create_and_sync(client, tmp_path, monkeypatch)
    assert first["added"] == 1 and first["documents"] == 1

    second = client.post(f"/api/v1/knowledge/sources/{source_id}/sync").json()["data"]
    assert second["unchanged"] == 1 and second["updated"] == 0

    architecture.write_text("# Runtime\n\nPlan versions are immutable and traceable.\n", encoding="utf-8")
    third = client.post(f"/api/v1/knowledge/sources/{source_id}/sync").json()["data"]
    assert third["updated"] == 1
    assert db_session.query(KnowledgeDocument).filter(KnowledgeDocument.source_id == source_id).count() == 1

    architecture.unlink()
    fourth = client.post(f"/api/v1/knowledge/sources/{source_id}/sync").json()["data"]
    assert fourth["deleted"] == 1
    document = db_session.query(KnowledgeDocument).filter(KnowledgeDocument.source_id == source_id).one()
    assert document.status == "deleted"
    assert {chunk.status for chunk in db_session.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id)} == {"disabled"}
    documents = client.get(f"/api/v1/knowledge/sources/{source_id}/documents").json()["data"]
    assert documents[0]["chunk_count"] >= 1
    chunks = client.get(f"/api/v1/knowledge/documents/{document.id}/chunks").json()["data"]
    assert chunks[0]["status"] == "disabled" and chunks[0]["content"]


def test_source_rejects_workspace_escape(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "workspace_root", str(tmp_path))
    response = client.post("/api/v1/knowledge/sources", json={
        "name": "Escape", "type": "workspace", "uri": "../outside",
    })
    assert response.status_code == 400
    assert "Workspace Root" in response.json()["detail"]["error"]["message"]


def test_hybrid_retrieval_persists_candidates_citations_and_budget_decisions(client, db_session, tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    (docs / "runtime.md").write_text(
        "# Runtime Architecture\n\nExecutionPlan versions are immutable and every replan keeps evidence.\n\n"
        "The scheduler executes dependency graphs and records task ready events.\n",
        encoding="utf-8",
    )
    source_id, _ = _create_and_sync(client, tmp_path, monkeypatch)
    response = client.post("/api/v1/context/retrieve", json={
        "query": "immutable ExecutionPlan replan evidence",
        "goal_id": "goal-1", "task_id": "task-1", "agent_id": "agent-1",
        "token_budget": 1000, "source_ids": [source_id], "workspace_scope": "docs/runtime.md",
    })
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["candidate_count"] >= 1
    assert data["items"][0]["citation"].startswith("docs/runtime.md#chunk-")
    assert data["token_count"] <= 1000
    run = db_session.query(RetrievalRun).filter(RetrievalRun.id == data["retrieval_run_id"]).one()
    records = db_session.query(RetrievedContextItem).filter(RetrievedContextItem.retrieval_run_id == run.id).all()
    assert run.policy == "hybrid_keyword_hash_embedding_v1"
    assert records and any(item.used for item in records)

    clipped = client.post("/api/v1/context/retrieve", json={
        "query": "immutable ExecutionPlan", "goal_id": "goal-1",
        "token_budget": 1, "source_ids": [source_id], "workspace_scope": "docs/**",
    }).json()["data"]
    assert clipped["candidate_count"] >= 1 and clipped["items"] == []
    assert db_session.query(RetrievedContextItem).filter(
        RetrievedContextItem.retrieval_run_id == clipped["retrieval_run_id"],
        RetrievedContextItem.used == False,
    ).count() >= 1


def test_disabled_or_out_of_scope_sources_return_traceable_empty_result(client, db_session, tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    (docs / "rule.md").write_text("Only approved architecture rules are trusted.", encoding="utf-8")
    source_id, _ = _create_and_sync(client, tmp_path, monkeypatch)

    out_of_scope = client.post("/api/v1/context/retrieve", json={
        "query": "architecture rules", "goal_id": "goal-empty",
        "source_ids": [source_id], "workspace_scope": "private/**",
    }).json()["data"]
    assert out_of_scope["candidate_count"] == 0 and out_of_scope["items"] == []

    assert client.patch(f"/api/v1/knowledge/sources/{source_id}/status", json={"status": "disabled"}).status_code == 200
    disabled = client.post("/api/v1/context/retrieve", json={
        "query": "architecture rules", "goal_id": "goal-empty", "source_ids": [source_id],
    }).json()["data"]
    assert disabled["candidate_count"] == 0
    runs = client.get("/api/v1/goals/goal-empty/context-runs").json()["data"]
    assert len(runs) == 2 and all(run["status"] == "empty" for run in runs)


def test_worker_context_uses_retrieval_gate_and_persists_snapshot(client, db_session, tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    (docs / "runtime.md").write_text("Scheduler dependencies are validated before task execution.", encoding="utf-8")
    _create_and_sync(client, tmp_path, monkeypatch)
    goal = Goal(id="context-goal", title="Fix scheduler dependencies", status="running", workspace_root=str(tmp_path))
    task = Task(id="context-task", goal_id=goal.id, title="Inspect scheduler dependencies", status="pending", task_type="coding")
    task.set_json("required_capabilities", ["code_read"])
    db_session.add_all([goal, task]); db_session.commit()

    package = build_context_package(db_session, goal, task)
    snapshot = persist_context_snapshot(db_session, "worker-1", None, package)
    db_session.commit()

    assert package["policy"] == "hybrid_keyword_hash_embedding_v1"
    assert package["knowledge_items"]
    assert package["citations"][0].startswith("docs/runtime.md#chunk-")
    assert package["retrieval_run_id"]
    stored = db_session.query(ContextPackageSnapshot).filter(ContextPackageSnapshot.id == snapshot.id).one()
    assert stored.retrieval_run_id == package["retrieval_run_id"]
    assert stored.token_count == package["token_count"]
    workspace = client.get(f"/api/v1/workspace/{goal.id}/state").json()["data"]
    task_state = next(item for item in workspace["tasks"] if item["id"] == task.id)
    assert task_state["context_runs"][0]["items"][0]["used"] is True
    assert task_state["context_runs"][0]["items"][0]["citation"].startswith("docs/runtime.md#chunk-")
