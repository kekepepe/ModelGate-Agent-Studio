"""V1.5 QL1-QL3: effectiveness loop — outcome votes, retrieval outcome
backfill, and ranking weight.

The machine-verifiable core of 'learns with use': a memory whose context
carried a verified task gains a success vote and outranks an identical
unvoted memory; a failed task hurts it.
"""
import json
import uuid

from src.models.knowledge import MemoryDraft, RetrievedContextItem
from src.models.workspace import Goal, Task
from src.services.context_service import build_context_package
from src.services.curator_service import (
    mark_retrieval_outcomes,
    record_memory_outcome,
)


def _memory(db_session, *, title, content, approved=True, success=0, failure=0):
    memory = MemoryDraft(
        id=str(uuid.uuid4()), type="project_memory", title=title, content=content,
        human_approved=approved, confidence=0.9,
        effectiveness_success=success, effectiveness_failure=failure,
    )
    db_session.add(memory)
    db_session.commit()
    return memory


def _task(db_session):
    goal = Goal(id=str(uuid.uuid4()), title="Effectiveness probe", status="running")
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Probe task", status="running")
    db_session.add_all([goal, task])
    db_session.commit()
    return goal, task


def test_verified_task_gives_success_vote(db_session):
    memory = _memory(db_session, title="Deploy windows", content="Deploy on Fridays only.")
    record_memory_outcome(
        db_session,
        json.dumps({"project_memories": [{"id": memory.id}]}),
        "completed_verified",
    )
    db_session.refresh(memory)
    assert memory.effectiveness_success == 1
    assert memory.effectiveness_failure == 0
    assert memory.effectiveness_rate == 1.0


def test_failed_task_gives_failure_vote(db_session):
    memory = _memory(db_session, title="Risky shortcut", content="Skip the test suite.")
    record_memory_outcome(
        db_session,
        json.dumps({"project_memories": [{"id": memory.id}]}),
        "failed",
    )
    db_session.refresh(memory)
    assert memory.effectiveness_failure == 1


def test_neutral_states_cast_no_vote(db_session):
    memory = _memory(db_session, title="Neutral", content="No vote either way.")
    record_memory_outcome(
        db_session,
        json.dumps({"project_memories": [{"id": memory.id}]}),
        "completed_unverified",
    )
    db_session.refresh(memory)
    assert memory.effectiveness_success == 0 and memory.effectiveness_failure == 0


def test_preferences_also_receive_votes(db_session):
    memory = _memory(db_session, title="Always pytest", content="pytest + fixtures.")
    record_memory_outcome(
        db_session,
        json.dumps({"user_preferences": [{"id": memory.id}]}),
        "completed_verified",
    )
    db_session.refresh(memory)
    assert memory.effectiveness_success == 1


def test_retrieval_outcomes_backfilled_used_and_ignored(db_session):
    run_id = str(uuid.uuid4())
    included = RetrievedContextItem(retrieval_run_id=run_id, source_type="knowledge", source_id="src-1", score=0.9, rank=1, used=True)
    excluded = RetrievedContextItem(retrieval_run_id=run_id, source_type="knowledge", source_id="src-2", score=0.05, rank=2, used=False)
    db_session.add_all([included, excluded])
    db_session.commit()

    mark_retrieval_outcomes(db_session, json.dumps({"retrieval_run_id": str(uuid.uuid4())}))  # other run → no-op
    mark_retrieval_outcomes(db_session, json.dumps({"retrieval_run_id": run_id}))

    db_session.expire_all()
    assert db_session.get(RetrievedContextItem, included.id).outcome == "used"
    assert db_session.get(RetrievedContextItem, excluded.id).outcome == "ignored"


def test_effectiveness_weight_breaks_ranking_ties(db_session):
    # Identical keyword relevance; the proven memory must outrank the
    # unvoted one in the context package.
    proven = _memory(db_session, title="Deploy windows", content="Effectiveness probe deploys happen on Fridays only.", success=6, failure=0)
    _memory(db_session, title="Deploy windows copy", content="Effectiveness probe deploys happen on Fridays only.", success=0, failure=0)
    goal, task = _task(db_session)

    package = build_context_package(db_session, goal, task)

    titles = [m["title"] for m in package["project_memories"]]
    assert titles and titles[0] == proven.title
