from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.core.database import Base

# Register every mapped table for autogenerate and baseline creation.
from src.models import agent as _agent  # noqa: F401
from src.models import handoff as _handoff  # noqa: F401
from src.models import knowledge as _knowledge  # noqa: F401
from src.models import model as _model  # noqa: F401
from src.models import quota as _quota  # noqa: F401
from src.models import selection as _selection  # noqa: F401
from src.models import supervisor as _supervisor  # noqa: F401
from src.models import tool as _tool  # noqa: F401
from src.models import workspace as _workspace  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
