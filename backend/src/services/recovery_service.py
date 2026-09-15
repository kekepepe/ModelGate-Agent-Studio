"""Recover expired Runtime work without replaying verified side effects."""

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.models.handoff import WorkerSession
from src.models.tool import ToolCallRecord
from src.models.workspace import Goal, Task
from src.services import log_service


NON_IDEMPOTENT_TOOL_NAMES = {"terminal_execute"}


def recover_interrupted_tasks(
    db: Session,
    goal_id: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, int]:
    moment = now or datetime.now(timezone.utc)
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        return {"recovered": 0, "approval_required": 0}

    recovered = 0
    approval_required = 0
    running = db.query(Task).filter(Task.goal_id == goal_id, Task.status == "running").all()
    for task in running:
        lease = task.lease_expires_at
        if lease is not None:
            comparable = lease if lease.tzinfo else lease.replace(tzinfo=timezone.utc)
            if comparable > moment:
                continue
        unsafe_effect = db.query(ToolCallRecord).filter(
            ToolCallRecord.task_id == task.id,
            ToolCallRecord.status == "completed",
            ToolCallRecord.tool_name.in_(NON_IDEMPOTENT_TOOL_NAMES),
            ToolCallRecord.idempotency_key.is_(None),
        ).first()
        if unsafe_effect:
            task.status = "waiting_approval"
            task.blocked_reason = (
                f"Recovery paused after non-idempotent tool '{unsafe_effect.tool_name}'. "
                "Confirm before replaying the Task."
            )
            approval_required += 1
        else:
            task.status = "pending"
            task.blocked_reason = "Recovered after an expired worker lease."
            recovered += 1
        task.lease_expires_at = None
        task.recovery_count = (task.recovery_count or 0) + 1
        if task.assigned_worker_id:
            worker = db.query(WorkerSession).filter(WorkerSession.id == task.assigned_worker_id).first()
            if worker and worker.status == "running":
                worker.status = "recoverable"
                worker.next_action = "approval" if unsafe_effect else "retry"
        log_service.create_log(db, {
            "goal_id": goal_id,
            "task_id": task.id,
            "event_type": "task.recovered",
            "event_status": task.status,
            "output_summary": task.blocked_reason,
            "metadata": {"recovery_count": task.recovery_count, "lease_expired_at": str(lease)},
        }, commit=False)
    if recovered or approval_required:
        db.commit()
    return {"recovered": recovered, "approval_required": approval_required}


# ---------------------------------------------------------------------------
# V1.4: standing recovery daemon (T2)
# ---------------------------------------------------------------------------

DAEMON_INTERVAL_SECONDS = 60
_daemon_thread = None
_daemon_stop = None


def recover_all_expired(db: Session) -> Dict[str, int]:
    """Scan every goal with expired running-task leases and recover them.

    Runs on the recovery daemon's cycle so a killed host process does not
    leave tasks stuck until someone manually re-runs a pipeline.
    """
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=5)
    expired_goals = (
        db.query(Goal.id)
        .join(Task, Task.goal_id == Goal.id)
        .filter(
            Task.status == "running",
            Task.lease_expires_at.isnot(None),
            Task.lease_expires_at < cutoff,
        )
        .all()
    )
    totals = {"recovered": 0, "approval_required": 0}
    for (goal_id,) in expired_goals:
        try:
            result = recover_interrupted_tasks(db, goal_id)
            totals["recovered"] += result.get("recovered", 0)
            totals["approval_required"] += result.get("approval_required", 0)
        except Exception:
            db.rollback()
            continue
    return totals


def start_recovery_daemon(
    app_logger=None,
    interval: int = DAEMON_INTERVAL_SECONDS,
    session_factory=None,
) -> None:
    """Start the in-process daemon thread (idempotent).

    Cycle: heartbeat-refresh every in-flight lease so live tasks are never
    mistaken for dead ones, then recover expired leases across all goals.
    `session_factory` is injectable for tests; production binds the app engine.
    """
    global _daemon_thread, _daemon_stop
    if _daemon_thread is not None and _daemon_thread.is_alive():
        return

    import threading

    if session_factory is None:
        from src.core.database import SessionLocal as session_factory

    _daemon_stop = threading.Event()

    def _cycle():
        while not _daemon_stop.wait(interval):
            session = session_factory()
            try:
                # Recovery only. Live tasks renew their own lease inside the
                # runtime loop — a daemon heartbeat here would also revive
                # genuinely dead leases, defeating the expiry signal.
                result = recover_all_expired(session)
                if result.get("recovered") or result.get("approval_required"):
                    if app_logger:
                        app_logger.info("recovery daemon cycle: %s", result)
            except Exception as exc:
                session.rollback()
                if app_logger:
                    app_logger.warning("recovery daemon cycle failed: %s", exc)
            finally:
                session.close()

    _daemon_thread = threading.Thread(target=_cycle, name="recovery-daemon", daemon=True)
    _daemon_thread.start()


def stop_recovery_daemon() -> None:
    global _daemon_thread, _daemon_stop
    if _daemon_stop is not None:
        _daemon_stop.set()
    _daemon_thread = None
