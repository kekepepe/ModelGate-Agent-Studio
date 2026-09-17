"""V1.5 QL6+QL7: conflict adjudication, confidence decay, skill auto-disable.

Governance never deletes user memories — conflicts are flagged and
resolved by a human; decay only lowers confidence; failing skills are
disabled and await review.
"""
import uuid

import pytest

from pytest import raises

from src.models.knowledge import MemoryDraft, SkillDraft
from src.services.curator_service import (
    _resolutions_conflict,
    decay_memories,
    disable_failing_skills,
    resolve_memory_conflict,
)


def test_same_error_class_conflicting_resolutions_flag_conflict(db_session):
    from datetime import datetime, timedelta, timezone

    from src.models.agent import AgentStation
    from src.models.handoff import ExecutionLog
    from src.models.workspace import Goal, Task
    from src.services.curator_service import generate_memories

    def seed_run(title, error, task_status):
        goal = Goal(id=str(uuid.uuid4()), title=title, status="completed")
        agent = AgentStation(id=str(uuid.uuid4()), name="Coder", role="coder", default_model_id="m", is_enabled=True)
        task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Build parser", status=task_status, assigned_agent_id=agent.id)
        log = ExecutionLog(goal_id=goal.id, task_id=task.id, agent_id=agent.id, event_type="error", event_status="failed", error_message=error)
        db_session.add_all([agent, goal, task, log])
        db_session.commit()
        return goal

    # First run recovers via retry; second run for the same error class ends unresolved.
    seed_run("Parser goal A", "Provider timeout after 3 attempts", "completed")
    generate_memories(db_session, db_session.query(Goal).order_by(Goal.created_at.asc()).first().id)
    seed_run("Parser goal B", "Provider timeout after 9 attempts", "failed")
    goal_b = db_session.query(Goal).order_by(Goal.created_at.desc()).first()
    generate_memories(db_session, goal_b.id)

    experience = db_session.query(MemoryDraft).filter(MemoryDraft.type == "experience_memory").one()
    assert experience.conflict_state == "conflict"
    assert "conflicting_resolution" in experience.get_metadata()


def test_conflict_never_flags_for_identical_resolutions():
    assert not _resolutions_conflict("Recovered via handoff; result: success.", "Recovered via handoff to X; result: success.")
    assert _resolutions_conflict("Recovered via handoff; result: success.", "Unresolved: the run ended without recovery.")
    assert not _resolutions_conflict("Unknown narrative.", "Recovered via handoff.")


def test_resolve_conflict_keeps_stored_by_default(db_session):
    memory = MemoryDraft(
        id=str(uuid.uuid4()), type="experience_memory",
        title="Experience: timeout", content="Error: timeout\nResolution: Recovered via handoff.",
        conflict_state="conflict",
    )
    metadata = {"error_signature": "abc", "resolution": "Recovered via handoff.", "occurrence_count": 2, "conflicting_resolution": "Unresolved: no recovery."}
    memory.set_metadata(metadata)
    db_session.add(memory)
    db_session.commit()

    result = resolve_memory_conflict(db_session, memory.id, keep="stored")

    assert result["conflict_state"] == "resolved"
    assert "Recovered via handoff" in result["content"]
    assert "Unresolved" not in result["content"]


def test_resolve_conflict_incoming_adopts_alternative(db_session):
    memory = MemoryDraft(
        id=str(uuid.uuid4()), type="experience_memory",
        title="Experience: timeout", content="Error: timeout\nResolution: Recovered via handoff.",
        conflict_state="conflict",
    )
    memory.set_metadata({"resolution": "Recovered via handoff.", "conflicting_resolution": "Unresolved: no recovery."})
    db_session.add(memory)
    db_session.commit()

    result = resolve_memory_conflict(db_session, memory.id, keep="incoming")

    assert result["conflict_state"] == "resolved"
    assert "Unresolved" in result["content"]


def test_resolve_rejects_non_conflicted_memory(db_session):
    memory = MemoryDraft(id=str(uuid.uuid4()), type="project_memory", title="Calm", content="fine")
    db_session.add(memory)
    db_session.commit()
    with raises(ValueError):
        resolve_memory_conflict(db_session, memory.id)


def test_decay_lowers_confidence_but_respects_floor_and_recent_hits(db_session):
    old_memory = MemoryDraft(id=str(uuid.uuid4()), type="project_memory", title="Old", content="stale", confidence=0.9, human_approved=True)
    old_memory.set_metadata({})  # never hit
    recent = MemoryDraft(id=str(uuid.uuid4()), type="project_memory", title="Fresh", content="hot", confidence=0.9, human_approved=True)
    from datetime import datetime, timedelta, timezone
    recent_memory = recent
    recent_memory.set_metadata({"last_hit_at": datetime.now(timezone.utc).isoformat()})
    floored = MemoryDraft(id=str(uuid.uuid4()), type="project_memory", title="Floor", content="low", confidence=0.21, human_approved=True)
    db_session.add_all([old_memory, recent_memory, floored])
    db_session.commit()

    result = decay_memories(db_session)

    assert result["decayed"] == 2  # old + floored (0.21*0.9=0.189 → floor 0.2)
    db_session.expire_all()
    assert db_session.get(MemoryDraft, old_memory.id).confidence == pytest.approx(0.81)
    assert db_session.get(MemoryDraft, recent_memory.id).confidence == 0.9
    assert db_session.get(MemoryDraft, floored.id).confidence == pytest.approx(0.2)


def test_failing_skills_auto_disable(db_session):
    failing = SkillDraft(id=str(uuid.uuid4()), name="Bad workflow", status="approved", human_approved=True, success_count=1, failure_count=5)
    healthy = SkillDraft(id=str(uuid.uuid4()), name="Good workflow", status="approved", human_approved=True, success_count=9, failure_count=3)
    db_session.add_all([failing, healthy])
    db_session.commit()

    result = disable_failing_skills(db_session)

    assert result["disabled"] == 1
    db_session.expire_all()
    assert db_session.get(SkillDraft, failing.id).status == "disabled"
    assert db_session.get(SkillDraft, healthy.id).status == "approved"

