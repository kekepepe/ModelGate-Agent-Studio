"""Initialize an empty database and verify the minimum API schema exists."""

import sys
from pathlib import Path

from sqlalchemy import inspect

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Importing the application loads every mapped model and executes the same
# first-run bootstrap path used by the deployed API.
from src.core.database import engine  # noqa: E402
from src.core.migrations import upgrade_database  # noqa: E402
from src.main import app as _app  # noqa: E402,F401


REQUIRED_TABLES = {
    "agent_stations",
    "execution_plans",
    "goals",
    "knowledge_sources",
    "tasks",
    "tool_call_records",
}


def main() -> None:
    upgrade_database()
    actual = set(inspect(engine).get_table_names())
    missing = REQUIRED_TABLES - actual
    if missing:
        raise SystemExit(f"Database smoke test failed; missing tables: {sorted(missing)}")
    print(f"Database smoke test passed ({len(actual)} tables)")


if __name__ == "__main__":
    main()
