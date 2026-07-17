import json
import uuid

from src.models.knowledge import SkillDraft
from src.models.workspace import Goal, Task
from src.services.curator_service import generate_memories, record_skill_outcome


def test_loaded_approved_skill_records_verified_outcomes(db_session):
    skill = SkillDraft(id=str(uuid.uuid4()), name="Fix API", status="approved", human_approved=True)
    db_session.add(skill)
    db_session.commit()
    context = json.dumps({"skills": [{"id": skill.id, "name": skill.name}]})
    record_skill_outcome(db_session, context, True)
    db_session.commit()
    db_session.refresh(skill)
    assert skill.success_count == 1
    assert skill.failure_count == 0
    assert skill.last_used_at is not None
    record_skill_outcome(db_session, context, False)
    db_session.commit()
    db_session.refresh(skill)
    assert skill.failure_count == 1


def test_verified_coding_path_creates_reviewable_skill_candidate(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Fix checkout validation", status="completed")
    plan = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Plan checkout fix", status="completed_unverified")
    code = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Implement checkout fix", status="completed_verified")
    db_session.add_all([goal, plan, code])
    db_session.commit()

    summary = generate_memories(db_session, goal.id, run_id="run-verified")

    assert summary["total_skills"] == 1
    skill = db_session.query(SkillDraft).one()
    assert skill.human_approved is None
    assert "verified task" in skill.success_criteria
