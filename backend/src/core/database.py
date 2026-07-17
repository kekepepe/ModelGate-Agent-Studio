from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./modelgate.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_runtime_v2_schema() -> None:
    """Apply additive Runtime v2 columns to an existing SQLite volume."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    additions = {
        "goals": {
            "execution_mode": "VARCHAR(20) NOT NULL DEFAULT 'live'", "workspace_root": "TEXT",
            "run_id": "VARCHAR(36)", "final_verification_status": "VARCHAR(50)",
            "budget_tokens": "INTEGER NOT NULL DEFAULT 100000", "budget_cost_usd": "FLOAT",
            "max_duration_seconds": "INTEGER NOT NULL DEFAULT 3600",
        },
        "tasks": {
            "task_type": "VARCHAR(50) NOT NULL DEFAULT 'general'", "required_capabilities": "TEXT NOT NULL DEFAULT '[]'",
            "required_tools": "TEXT NOT NULL DEFAULT '[]'", "dependencies": "TEXT NOT NULL DEFAULT '[]'",
            "acceptance_criteria": "TEXT NOT NULL DEFAULT '[]'", "risk_level": "VARCHAR(20) NOT NULL DEFAULT 'low'",
            "retry_count": "INTEGER NOT NULL DEFAULT 0", "max_retries": "INTEGER NOT NULL DEFAULT 2",
            "verification_status": "VARCHAR(50)", "blocked_reason": "TEXT", "parent_task_id": "VARCHAR(36)",
        },
        "worker_sessions": {
            "workspace_scope": "TEXT", "step_count": "INTEGER NOT NULL DEFAULT 0",
            "failure_count": "INTEGER NOT NULL DEFAULT 0", "last_observation": "TEXT", "next_action": "TEXT",
        },
        "agent_stations": {
            "max_tokens_per_task": "INTEGER NOT NULL DEFAULT 32000",
            "max_duration_seconds": "INTEGER NOT NULL DEFAULT 900",
            "max_consecutive_failures": "INTEGER NOT NULL DEFAULT 3",
        },
        "tool_call_records": {"result_data": "TEXT NOT NULL DEFAULT '{}'"},
        "memory_drafts": {"expires_at": "DATETIME"},
        "skill_drafts": {
            "version": "VARCHAR(50) NOT NULL DEFAULT '1.0'", "success_count": "INTEGER NOT NULL DEFAULT 0",
            "failure_count": "INTEGER NOT NULL DEFAULT 0", "last_used_at": "DATETIME",
        },
        "runtime_runs": {
            "budget_tokens": "INTEGER NOT NULL DEFAULT 100000", "budget_cost_usd": "FLOAT",
            "max_duration_seconds": "INTEGER NOT NULL DEFAULT 3600",
        },
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table, columns in additions.items():
            if table not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
