"""V1.2 M2: execution experience sedimentation + explicit user preferences.

Errors become deduplicated experience memories with a resolution narrative
(the Mem0-style UPDATE-on-merge), and explicit user preferences are born
approved and durable so context building can inject them unconditionally.
"""
import uuid

from pytest import raises

from src.models.agent import AgentStation
from src.models.handoff import ExecutionLog, HandoffRecord
from src.models.knowledge import MemoryDraft
from src.models.workspace import Goal, Task
from src.services import memory_vector_service
from src.services.curator_service import (
    _error_signature,
    create_user_preference,
    generate_memories,
)


def _goal_with_error(db_session, *, title, error_message, task_status="completed", with_handoff=False):
    goal = Goal(id=str(uuid.uuid4()), title=title, status="completed")
    agent = AgentStation(
        id=str(uuid.uuid4()), name="Coder", role="coder",
        default_model_id="m-1", is_enabled=True,
    )
    task = Task(
        id=str(uuid.uuid4()), goal_id=goal.id, title="Build parser",
        description="Parser work", status=task_status, assigned_agent_id=agent.id,
    )
    db_session.add_all([agent, goal, task])
    db_session.flush()
    log = ExecutionLog(
        goal_id=goal.id, task_id=task.id, agent_id=agent.id,
        event_type="error", event_status="failed",
        error_message=error_message,
    )
    rows = [log]
    if with_handoff:
        rows.append(HandoffRecord(
            goal_id=goal.id, task_id=task.id,
            from_agent_id=agent.id, from_model_id="m-1",
            to_agent_id=agent.id, to_model_id="m-1",
            reason="error", status="completed",
            result_after_handoff="success",
        ))
    db_session.add_all(rows)
    db_session.commit()
    return goal, task


def test_error_log_becomes_experience_memory(db_session):
    goal, _ = _goal_with_error(
        db_session, title="Parser goal",
        error_message="Provider timeout after 3 attempts (req 8f2a1b2c)",
        task_status="completed",
    )

    generate_memories(db_session, goal.id, run_id="run-exp-1")

    experience = db_session.query(MemoryDraft).filter(
        MemoryDraft.type == "experience_memory",
    ).one()
    assert "Provider timeout after 3 attempts" in experience.content
    assert experience.get_metadata()["occurrence_count"] == 1
    assert experience.get_metadata()["error_signature"]
    assert experience.get_metadata()["resolution"] == (
        "Task eventually completed after the error (retry within the run)."
    )
    assert experience.get_embedding(), "experience must enter the RAG pipeline embedded"


def test_same_signature_merges_occurrences_across_goals(db_session):
    goal_a, _ = _goal_with_error(
        db_session, title="Goal A",
        error_message="Provider timeout after 3 attempts (req 8f2a1b2c)",
    )
    goal_b, _ = _goal_with_error(
        db_session, title="Goal B",
        error_message="Provider timeout after 99 attempts (req 77ff00aa)",
    )

    generate_memories(db_session, goal_a.id, run_id="run-a")
    generate_memories(db_session, goal_b.id, run_id="run-b")

    experiences = db_session.query(MemoryDraft).filter(
        MemoryDraft.type == "experience_memory",
    ).all()
    assert len(experiences) == 1, "same error class must merge, not duplicate"
    assert experiences[0].get_metadata()["occurrence_count"] == 2


def test_unresolved_error_keeps_low_confidence(db_session):
    goal, _ = _goal_with_error(
        db_session, title="Doomed goal",
        error_message="Sandbox rejected the command: rm -rf /",
        task_status="failed",
    )

    generate_memories(db_session, goal.id, run_id="run-doom")

    experience = db_session.query(MemoryDraft).filter(
        MemoryDraft.type == "experience_memory",
    ).one()
    assert experience.get_metadata()["resolution"].startswith("Unresolved")
    assert experience.confidence == 0.4


def test_handoff_recovery_is_the_resolution(db_session):
    goal, _ = _goal_with_error(
        db_session, title="Handoff rescue",
        error_message="Model refused the payload format",
        task_status="running",
        with_handoff=True,
    )

    generate_memories(db_session, goal.id, run_id="run-handoff")

    experience = db_session.query(MemoryDraft).filter(
        MemoryDraft.type == "experience_memory",
    ).one()
    assert experience.get_metadata()["resolution"].startswith("Recovered via handoff")


def test_error_signature_ignores_numbers_and_ids():
    assert (
        _error_signature("Provider timeout after 3 attempts (req 8f2a1b2c)")
        == _error_signature("provider TIMEOUT after 99 attempts (req 77ff00aa)")
    )
    assert (
        _error_signature("Sandbox rejected: rm -rf /")
        != _error_signature("Sandbox approved: ls -la")
    )


def test_create_user_preference_is_approved_and_embedded(db_session):
    preference = create_user_preference(
        db_session,
        title="Always pytest",
        content="User prefers pytest with fixtures over unittest classes.",
        created_by="mavis",
    )
    assert preference.type == "user_preference"
    assert preference.human_approved is True
    assert preference.expires_at is None
    assert preference.get_embedding(), "preferences must be embedded on creation"

    with raises(ValueError):
        create_user_preference(db_session, title=" ", content="missing title")
