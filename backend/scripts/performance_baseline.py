# ruff: noqa: E402
"""Deterministic local load baseline for Workspace, Retrieval, and Scheduler.

Run from ``backend`` with:
    docker compose --profile verify run --rm --entrypoint python backend-verify scripts/performance_baseline.py

The database URL is intentionally disposable. The script recreates all tables.
"""

from __future__ import annotations

import json
import os
import resource
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, List

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import event

from src.core.database import Base, SessionLocal, engine
from src.models import handoff as _handoff_models  # noqa: F401
from src.models import knowledge as _knowledge_models  # noqa: F401
from src.models import selection as _selection_models  # noqa: F401
from src.models import supervisor as _supervisor_models  # noqa: F401
from src.models import tool as _tool_models  # noqa: F401
from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog
from src.models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeSource
from src.models.workspace import Goal, Task
from src.services import retrieval_service, scheduler_service, workspace_service


QUERY_COUNT = 0


@event.listens_for(engine, "before_cursor_execute")
def _count_query(*_args):
    global QUERY_COUNT
    QUERY_COUNT += 1


def _percentile(values: List[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return round(ordered[index], 2)


def _run_load(name: str, total: int, concurrency: int, operation: Callable[[int], None]) -> Dict:
    global QUERY_COUNT
    start_queries = QUERY_COUNT
    cpu_start = time.process_time()
    wall_start = time.perf_counter()
    latencies: List[float] = []
    errors: List[str] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {}
        for index in range(total):
            started = time.perf_counter()

            def invoke(item=index, timestamp=started):
                operation(item)
                return (time.perf_counter() - timestamp) * 1000

            futures[pool.submit(invoke)] = index
        for future in as_completed(futures):
            try:
                latencies.append(future.result())
            except Exception as exc:  # benchmark output must retain every failure
                errors.append(f"{type(exc).__name__}: {exc}")
    wall_ms = (time.perf_counter() - wall_start) * 1000
    cpu_ms = (time.process_time() - cpu_start) * 1000
    queries = QUERY_COUNT - start_queries
    return {
        "name": name,
        "requests": total,
        "concurrency": concurrency,
        "p50_ms": _percentile(latencies, 0.50),
        "p95_ms": _percentile(latencies, 0.95),
        "p99_ms": _percentile(latencies, 0.99),
        "wall_ms": round(wall_ms, 2),
        "cpu_ms": round(cpu_ms, 2),
        "error_rate": round(len(errors) / total, 4),
        "db_queries": queries,
        "queries_per_request": round(queries / total, 2),
        "sample_errors": errors[:3],
    }


def _seed() -> List[str]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        goal_ids = []
        agent = AgentStation(
            id="load-agent", name="Load Agent", role="coder",
            default_model_id="load-model", is_enabled=True, max_concurrency=5,
        )
        db.add(agent)
        for goal_index in range(10):
            goal_id = f"load-goal-{goal_index}"
            goal_ids.append(goal_id)
            db.add(Goal(
                id=goal_id, title=f"Load goal {goal_index}", status="running",
                execution_mode="mock", max_parallel_tasks=5,
            ))
            tasks = []
            for task_index in range(100):
                task = Task(
                    id=f"load-task-{goal_index}-{task_index}", goal_id=goal_id,
                    title=f"Task {task_index}: bounded workspace serialization",
                    description="A deterministic task used for production load baselining.",
                    status="completed_verified", assigned_agent_id=agent.id,
                    task_type="direct", output="verified output",
                    verification_status="passed", duration_ms=task_index + 1,
                )
                tasks.append(task)
            db.add_all(tasks)
        for index in range(500):
            db.add(ExecutionLog(
                goal_id="load-goal-0",
                task_id=f"load-task-0-{index % 100}",
                event_type="agent_step",
                event_status="completed",
                output_summary=f"Load event {index}",
            ))

        source = KnowledgeSource(
            id="load-source", name="Load corpus", type="workspace",
            uri="load://corpus", status="active",
        )
        document = KnowledgeDocument(
            id="load-document", source_id=source.id, path="LOAD.md",
            title="Load corpus", checksum="load-checksum", status="indexed",
        )
        db.add_all([source, document])
        for index in range(100):
            db.add(KnowledgeChunk(
                id=f"load-chunk-{index}", document_id=document.id,
                content=f"runtime architecture scheduler agent task evidence item {index}",
                chunk_index=index, token_count=12, status="active",
            ))
        db.commit()
        return goal_ids
    finally:
        db.close()


def _workspace(goal_ids: List[str], index: int) -> None:
    db = SessionLocal()
    try:
        state = workspace_service.get_workspace_state(db, goal_ids[index % len(goal_ids)])
        if len(state["tasks"]) != 100:
            raise AssertionError("workspace task count changed")
    finally:
        db.close()


def _retrieve(index: int) -> None:
    db = SessionLocal()
    try:
        result = retrieval_service.retrieve(
            db,
            query=f"runtime architecture scheduler agent task evidence item {index % 100}",
            goal_id=f"load-goal-{index % 10}",
            token_budget=300,
            limit=5,
        )
        if not result["items"]:
            raise AssertionError("retrieval unexpectedly returned no results")
    finally:
        db.close()


def _scheduler_fixture(worker_count: int) -> None:
    db = SessionLocal()
    try:
        goal = Goal(
            id=str(uuid.uuid4()),
            title="Scheduler load", status="running", max_parallel_tasks=worker_count,
        )
        db.add(goal)
        for index in range(worker_count):
            agent_id = str(uuid.uuid4())
            agent = AgentStation(
                id=agent_id, name=f"Scheduler {index}", role="coder",
                default_model_id="load-model", is_enabled=True, max_concurrency=1,
            )
            task = Task(
                id=str(uuid.uuid4()), goal_id=goal.id, title=f"Parallel {index}",
                status="pending", assigned_agent_id=agent.id,
            )
            task.set_json("required_capabilities", ["parallel_safe"])
            db.add_all([agent, task])
        db.commit()
        decision = scheduler_service.schedule_ready_tasks(db, goal)
        if len(decision.selected_tasks) != worker_count:
            raise AssertionError("scheduler did not honor worker capacity")
    finally:
        db.close()


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url or "performance" not in database_url:
        raise SystemExit("Use an explicit disposable DATABASE_URL containing 'performance'.")
    goal_ids = _seed()
    results = []
    for concurrency in (10, 25, 50):
        results.append(_run_load(
            f"workspace_{concurrency}", concurrency, concurrency,
            lambda index: _workspace(goal_ids, index),
        ))
    results.append(_run_load("ten_goals", 10, 10, lambda index: _workspace(goal_ids, index)))
    results.append(_run_load("retrieval_50", 50, 50, _retrieve))
    for workers in (1, 3, 5):
        results.append(_run_load(
            f"scheduler_{workers}_workers", 5, 1,
            lambda _index, count=workers: _scheduler_fixture(count),
        ))

    peak_memory_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if os.uname().sysname != "Darwin":
        peak_memory_mb /= 1024
    else:
        peak_memory_mb /= 1024 * 1024
    payload = {
        "database": database_url.split("@")[-1],
        "fixture": {"goals": 10, "tasks": 1000, "logs": 500, "knowledge_chunks": 100},
        "peak_memory_mb": round(peak_memory_mb, 2),
        "results": results,
        "gate": {
            "max_error_rate": 0,
            "workspace_p95_ms": 1500,
            "retrieval_p95_ms": 1500,
        },
    }
    failed = any(item["error_rate"] > 0 for item in results)
    failed = failed or any(
        item["p95_ms"] > 1500
        for item in results if item["name"].startswith(("workspace", "retrieval"))
    )
    payload["passed"] = not failed
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
