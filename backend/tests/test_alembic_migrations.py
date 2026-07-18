import os
import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _upgrade(database_url: str) -> None:
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.upgrade(Config(str(BACKEND_ROOT / "alembic.ini")), "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


def test_empty_database_and_repeat_upgrade(tmp_path):
    database = tmp_path / "empty.db"
    url = f"sqlite:///{database}"
    _upgrade(url)
    _upgrade(url)
    engine = create_engine(url)
    inspector = inspect(engine)
    assert "execution_plans" in inspector.get_table_names()
    assert "knowledge_sources" in inspector.get_table_names()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0009_model_provider_fields"


def test_legacy_012_database_upgrades_without_losing_runtime_records(tmp_path):
    database = tmp_path / "legacy-012.db"
    connection = sqlite3.connect(database)
    try:
        for migration in sorted((BACKEND_ROOT / "migrations").glob("*.sql"))[:12]:
            connection.executescript(migration.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO agent_stations (id,name,role,default_model_id,system_prompt) VALUES (?,?,?,?,?)",
            ("agent-1", "Coder", "coder", "model-1", "code"),
        )
        connection.execute(
            "INSERT INTO goals (id,title,status,created_at,updated_at) VALUES (?,?,?,?,?)",
            ("goal-1", "Preserve me", "running", "2026-07-01", "2026-07-01"),
        )
        connection.execute(
            "INSERT INTO tasks (id,goal_id,title,status,created_at,updated_at) VALUES (?,?,?,?,?,?)",
            ("task-1", "goal-1", "Legacy task", "running", "2026-07-01", "2026-07-01"),
        )
        connection.commit()
    finally:
        connection.close()

    url = f"sqlite:///{database}"
    _upgrade(url)
    engine = create_engine(url)
    inspector = inspect(engine)
    assert {"api_key", "api_base_url"} <= {column["name"] for column in inspector.get_columns("models")}
    assert "plan_version_id" in {column["name"] for column in inspector.get_columns("tasks")}
    assert "max_parallel_tasks" in {column["name"] for column in inspector.get_columns("goals")}
    assert "capability_profile" in {column["name"] for column in inspector.get_columns("agent_stations")}
    with engine.connect() as upgraded:
        assert upgraded.execute(text("SELECT title FROM goals WHERE id='goal-1'")).scalar_one() == "Preserve me"
        assert upgraded.execute(text("SELECT title FROM tasks WHERE id='task-1'")).scalar_one() == "Legacy task"
