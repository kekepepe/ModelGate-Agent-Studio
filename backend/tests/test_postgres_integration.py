"""Portable migration and ORM smoke tests against a real PostgreSQL server."""

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.models.tool import ToolCallRecord
from src.models.workspace import Goal, Task


@pytest.mark.integration
def test_postgres_migration_constraints_and_rollback():
    database_url = os.environ.get("POSTGRES_TEST_URL")
    if not database_url:
        pytest.skip("POSTGRES_TEST_URL is required for the PostgreSQL integration gate")

    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        config = Config("alembic.ini")
        command.upgrade(config, "head")
        command.upgrade(config, "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous

    engine = create_engine(database_url)
    assert "execution_plans" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0008_worktree_audit"

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        goal = Goal(id="postgres-goal", title="PostgreSQL integration", status="running")
        task = Task(id="postgres-task", goal_id=goal.id, title="Portable ORM", status="pending")
        first = ToolCallRecord(
            id="postgres-tool-1", goal_id=goal.id, task_id=task.id,
            tool_name="file_write", tool_input="{}", status="completed",
            idempotency_key="postgres-idempotency-key",
        )
        session.add_all([goal, task, first])
        session.commit()

        duplicate = ToolCallRecord(
            id="postgres-tool-2", goal_id=goal.id, task_id=task.id,
            tool_name="file_write", tool_input="{}", status="completed",
            idempotency_key="postgres-idempotency-key",
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        assert session.query(Goal).filter(Goal.id == goal.id).one().title == "PostgreSQL integration"
        assert session.query(Task).filter(Task.id == task.id).one().status == "pending"
    finally:
        session.close()
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE TABLE tool_call_records, tasks, goals RESTART IDENTITY CASCADE"))
        engine.dispose()
