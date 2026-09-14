"""V1.2 M4: hybrid context ranking, success-rate weighting, preference
injection, and experience recall on the replan path."""
import uuid

from src.models.knowledge import MemoryDraft, SkillDraft
from src.models.workspace import Goal, Task
from src.services.context_service import (
    build_context_package,
    build_planning_context,
    build_replan_context,
)
from src.services.curator_service import create_user_preference


def _task(db_session, *, title="Build login page", capabilities=None):
    goal = Goal(id=str(uuid.uuid4()), title="Ship the auth system", status="running")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title=title, status="pending")
    if capabilities:
        task.set_json("required_capabilities", capabilities)
    db_session.add_all([goal, task])
    db_session.commit()
    return goal, task


def _approved_skill(db_session, *, name, scenario, success_count, failure_count, status="approved", human_approved=True):
    skill = SkillDraft(
        id=str(uuid.uuid4()), name=name, scenario=scenario,
        status=status, human_approved=human_approved,
        success_count=success_count, failure_count=failure_count,
    )
    skill.set_steps(["step one", "step two", "step three", "step four"])
    db_session.add(skill)
    db_session.commit()
    return skill


def test_user_preferences_are_injected_unconditionally(db_session):
    create_user_preference(
        db_session, title="Always pytest",
        content="User prefers pytest with fixtures over unittest classes.",
    )
    # A task whose wording shares nothing with the preference.
    goal, task = _task(db_session, title="Completely unrelated widget work")

    package = build_context_package(db_session, goal, task)

    assert [p["title"] for p in package["user_preferences"]] == ["Always pytest"]
    assert package["project_memories"] == [], "no keyword/vector match expected here"
    assert "matched" not in package["retrieval_reason"] or "gated off" in package["retrieval_reason"] or \
        package["retrieval_reason"].startswith(("No project", "Task capability", "Knowledge RAG"))


def test_skill_success_rate_weights_ranking(db_session):
    # Equal keyword relevance; the proven skill must outrank the failing one.
    proven = _approved_skill(db_session, name="Deploy checklist", scenario="Shipping to production",
                             success_count=8, failure_count=0)
    failing = _approved_skill(db_session, name="Deploy quickpath", scenario="Deploy to production quickly",
                              success_count=0, failure_count=8)
    goal, task = _task(db_session, title="Deploy to production")

    package = build_context_package(db_session, goal, task)

    ids = [item["id"] for item in package["skills"]]
    assert ids == [proven.id, failing.id]
    assert package["skills"][0]["success_rate"] == 1.0
    assert package["skills"][0]["steps_total"] == 4
    assert len(package["skills"][0]["steps"]) == 3, "progressive disclosure caps steps in context"


def test_planning_context_suggests_high_success_skills(db_session):
    _approved_skill(db_session, name="Auth bootstrapping", scenario="New auth system setup",
                    success_count=5, failure_count=0)
    goal, _task_unused = _task(db_session, title="New auth system")

    package = build_planning_context(db_session, goal)

    assert package["skills"], "planning should receive skill suggestions"
    assert package["skills"][0]["name"] == "Auth bootstrapping"


def test_replan_context_recalls_similar_experience(db_session):
    experience = MemoryDraft(
        id=str(uuid.uuid4()), type="experience_memory",
        title="Experience: Provider timeout after retries",
        content="Error: Provider timeout after retries\nResolution: Recovered via handoff; result: success.",
        confidence=0.7, human_approved=True,
    )
    experience.set_metadata({"error_signature": "abc123", "occurrence_count": 2})
    db_session.add(experience)
    db_session.commit()

    goal = Goal(id=str(uuid.uuid4()), title="Timeout recovery", status="running")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Timeout recovery step", status="failed")
    db_session.add_all([goal, task])
    db_session.commit()

    package = build_replan_context(db_session, goal, [task], reason="Provider timeout after retries")

    assert package["experiences"], "replan must recall similar past experiences"
    assert package["experiences"][0]["error_signature"] == "abc123"
    assert "Recovered via handoff" in package["experiences"][0]["content"]
