"""Run the repository-owned Alembic chain before application bootstrap."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def alembic_config() -> Config:
    backend_root = Path(__file__).resolve().parents[2]
    return Config(str(backend_root / "alembic.ini"))


def upgrade_database() -> None:
    command.upgrade(alembic_config(), "head")
