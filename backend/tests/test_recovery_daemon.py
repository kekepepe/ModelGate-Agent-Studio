"""V1.4 T2: standing recovery daemon.

A killed host process leaves running tasks with expired leases; the
daemon heartbeats live leases and recovers expired ones across all
goals without waiting for a manual pipeline run.
"""
import time
import uuid

from src.models.agent import AgentStation
from src.models.workspace import Goal, Task
from src.services.recovery_service import (
    recover_all_expired,
    start_recovery_daemon,
    stop_recovery_daemon,
)


def _running_task_with_expired_lease(db_session, title="stuck"):
    goal = Goal(id=str(uuid.uuid4()), title=f"Recovery {title}", status="running")
    agent = AgentStation(
        id=str(uuid.uuid4()), name="Coder", role="coder",
        default_model_id="m-1", is_enabled=True,
    )
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title=f"{title} task",
        description="left running by a dead host", status="running",
        assigned_agent_id=agent.id,
    )
    # lease already expired (expires_at in the past)
    from datetime import datetime, timedelta, timezone

    task.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.add_all([agent, goal, task])
    db_session.commit()
    return goal, task


def test_recover_all_expired_recovers_across_goals(db_session):
    _running_task_with_expired_lease(db_session, "goal A")
    _running_task_with_expired_lease(db_session, "goal B")

    totals = recover_all_expired(db_session)

    assert totals["recovered"] == 2
    from src.models.workspace import Task

    statuses = [t.status for t in db_session.query(Task).all()]
    assert set(statuses) == {"pending"}


def test_live_lease_is_heartbeated_not_recovered(db_session):
    from datetime import datetime, timedelta, timezone

    goal, task = _running_task_with_expired_lease(db_session, "live")
    # refresh the lease so it is genuinely live
    task.lease_expires_at = datetime.now(timezone.utc) + timedelta(seconds=120)
    db_session.commit()

    recover_all_expired(db_session)

    db_session.refresh(task)
    assert task.status == "running", "live leases must not be recovered"


def test_daemon_recovers_expired_task_within_interval(db_session):
    _running_task_with_expired_lease(db_session, "daemon")

    # Short interval for the test; daemon thread is a daemon so the pytest
    # process exits regardless. Idempotent start; stop at the end.
    from src.services import recovery_service
    from tests.conftest import TestingSessionLocal

    cycles = []
    sf_errors = []
    original = recovery_service.recover_all_expired
    recovery_service.recover_all_expired = lambda db: cycles.append(1) or original(db)

    def probing_factory():
        try:
            return TestingSessionLocal()
        except Exception as exc:
            sf_errors.append(repr(exc))
            raise

    try:
        # conftest's src.main import already started the 60s production daemon;
        # stop it so this test's 1s daemon actually runs.
        stop_recovery_daemon()
        start_recovery_daemon(interval=1, session_factory=probing_factory)
        deadline = time.time() + 5
        from src.models.workspace import Task

        recovered = False
        while time.time() < deadline:
            task = db_session.query(Task).filter(Task.status == "pending").first()
            if task is not None:
                recovered = True
                break
            time.sleep(0.2)
        assert recovered, f"daemon did not recover within 5s (cycles: {len(cycles)}, sf_errors: {sf_errors[:2]})"
    finally:
        recovery_service.recover_all_expired = original
        stop_recovery_daemon()


def test_daemon_start_is_idempotent(db_session):
    start_recovery_daemon(interval=3600)
    first = stop_recovery_daemon
    start_recovery_daemon(interval=3600)  # must not spawn a second thread
    stop_recovery_daemon()
    assert first is stop_recovery_daemon
