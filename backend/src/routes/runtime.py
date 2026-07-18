import json
import threading
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.core.database import SessionLocal, get_db
from src.models.handoff import ExecutionLog
from src.models.workspace import Goal
from src.services import goal_service, log_service, runtime_service

router = APIRouter(tags=["runtime"])


def _success(data, status_code=200):
    return {"success": True, "data": data}


def _error(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.post("/runtime/execute/{goal_id}")
def execute_goal(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = runtime_service.execute_goal_pipeline(db, goal_id)
        return _success(result)
    except goal_service.GoalNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except runtime_service.GoalNotReadyError as e:
        _error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


def _background_execute_goal(goal_id: str) -> None:
    """Use an independent DB session because the request session is closed."""
    db = SessionLocal()
    try:
        runtime_service.execute_goal_pipeline(db, goal_id)
    except Exception as exc:
        log_service.create_log(db, {
            "goal_id": goal_id, "event_type": "error", "event_status": "failed",
            "error_message": f"Background runtime failed: {exc}",
        })
        goal = db.query(Goal).filter(Goal.id == goal_id).first()
        if goal and goal.status == "running":
            goal.status = "failed"
            db.commit()
    finally:
        db.close()


@router.post("/runtime/start/{goal_id}", status_code=202)
def start_goal_async(goal_id: str, db: Session = Depends(get_db)):
    """Queue a runtime run without holding the HTTP connection open."""
    try:
        goal = goal_service.get_goal(db, goal_id)
        if goal.status not in ("planning", "running"):
            raise runtime_service.GoalNotReadyError(
                f"Goal must be planning or running, current: {goal.status}"
            )
        runtime_service.ensure_plan_confirmed(db, goal_id)
        goal.status = "running"
        db.commit()
        threading.Thread(target=_background_execute_goal, args=(goal_id,), daemon=True).start()
        return _success({"goal_id": goal_id, "status": "running"}, status_code=202)
    except goal_service.GoalNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)
    except runtime_service.GoalNotReadyError as exc:
        _error("BAD_REQUEST", str(exc), 400)


@router.post("/runtime/execute-step/{task_id}")
def execute_step(task_id: str, db: Session = Depends(get_db)):
    try:
        result = runtime_service.execute_task_step(db, task_id)
        return _success(result)
    except runtime_service.TaskNotReadyError as e:
        _error("BAD_REQUEST", str(e), 400)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


@router.post("/runtime/pause/{goal_id}")
def pause_goal(goal_id: str, db: Session = Depends(get_db)):
    try:
        return _success(runtime_service.pause_goal_run(db, goal_id))
    except goal_service.GoalNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except runtime_service.GoalNotReadyError as e:
        _error("BAD_REQUEST", str(e), 400)


@router.post("/runtime/resume/{goal_id}")
def resume_goal(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = runtime_service.resume_goal_run(db, goal_id)
        if result["status"] == "running":
            threading.Thread(target=_background_execute_goal, args=(goal_id,), daemon=True).start()
        return _success(result)
    except goal_service.GoalNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except runtime_service.GoalNotReadyError as e:
        _error("BAD_REQUEST", str(e), 400)


@router.post("/runtime/stop/{goal_id}")
def stop_goal(goal_id: str, db: Session = Depends(get_db)):
    try:
        return _success(runtime_service.stop_goal_run(db, goal_id))
    except goal_service.GoalNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except runtime_service.GoalNotReadyError as e:
        _error("BAD_REQUEST", str(e), 400)


@router.get("/runtime/status/{goal_id}")
def get_runtime_status(goal_id: str, db: Session = Depends(get_db)):
    try:
        result = runtime_service.get_runtime_status(db, goal_id)
        return _success(result)
    except goal_service.GoalNotFoundError as e:
        _error("NOT_FOUND", str(e), 404)
    except Exception as e:
        _error("INTERNAL_ERROR", str(e), 500)


@router.get("/runtime/events/{goal_id}")
def stream_runtime_events(
    goal_id: str,
    after_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Expose persisted runtime events as SSE for a truthful live console.

    Events are emitted only after Runtime has persisted them, so a UI never
    needs to infer work from animation or from a model's unverified prose.
    Clients can reconnect with the last event id they processed.
    """
    try:
        goal_service.get_goal(db, goal_id)
    except goal_service.GoalNotFoundError as exc:
        _error("NOT_FOUND", str(exc), 404)

    after_created_at = None
    if after_id:
        previous = db.query(ExecutionLog).filter(
            ExecutionLog.id == after_id, ExecutionLog.goal_id == goal_id,
        ).first()
        if previous:
            after_created_at = previous.created_at

    def event_stream():
        seen = set()
        while True:
            query = db.query(ExecutionLog).filter(ExecutionLog.goal_id == goal_id)
            if after_created_at:
                query = query.filter(ExecutionLog.created_at >= after_created_at)
            for log in query.order_by(ExecutionLog.created_at.asc()).all():
                if log.id in seen or log.id == after_id:
                    continue
                seen.add(log.id)
                payload = {
                    "id": log.id, "goal_id": log.goal_id, "task_id": log.task_id,
                    "event_type": log.event_type, "event_status": log.event_status,
                    "summary": log.output_summary or log.input_summary or log.error_message,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                yield "event: runtime\ndata: " + json.dumps(payload, ensure_ascii=False) + "\n\n"
            goal = db.query(Goal).filter(Goal.id == goal_id).first()
            if not goal or goal.status in {"completed", "failed", "paused", "cancelled"}:
                yield "event: end\ndata: {}\n\n"
                break
            yield ": keepalive\n\n"
            time.sleep(0.25)

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
