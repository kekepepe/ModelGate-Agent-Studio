"""Idempotent helpers for upgrading legacy SQLite installations."""

from alembic import op
import sqlalchemy as sa


def has_table(table_name: str) -> bool:
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return has_table(table_name) and column_name in {column["name"] for column in inspector.get_columns(table_name)}


def add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if has_table(table_name) and not has_column(table_name, column.name):
        op.add_column(table_name, column)


def create_index_if_missing(name: str, table_name: str, columns: list[str], *, unique: bool = False) -> None:
    if not has_table(table_name):
        return
    existing = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}
    if name not in existing and all(has_column(table_name, column) for column in columns):
        op.create_index(name, table_name, columns, unique=unique)
