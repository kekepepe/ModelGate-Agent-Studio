"""V1.4 T1: SQLite WAL pragmas + parallel write contention regression.

The parallel runtime's worker sessions hammer the same SQLite file from
multiple threads; WAL + busy_timeout must turn that into clean concurrent
commits instead of 'database is locked'.
"""
import threading

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.models.workspace import Goal


def _engine_with_wal(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/wal-test.db",
        connect_args={"check_same_thread": False, "timeout": 5},
    )
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


def test_wal_mode_is_active(tmp_path):
    engine = _engine_with_wal(tmp_path)
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA journal_mode")).scalar() == "wal"


def test_eight_thread_concurrent_commits_without_database_locked(tmp_path):
    engine = _engine_with_wal(tmp_path)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    threads, errors = [], []
    THREADS, WRITES = 8, 10

    def worker(index):
        try:
            for iteration in range(WRITES):
                session = factory()
                try:
                    session.add(Goal(
                        id=f"goal-{index}-{iteration}",
                        title=f"parallel write {index}/{iteration}",
                        status="running",
                    ))
                    session.commit()
                finally:
                    session.close()
        except Exception as exc:  # pragma: no cover - surfaces the failure
            errors.append(exc)

    for index in range(THREADS):
        thread = threading.Thread(target=worker, args=(index,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent commits raised: {errors[:3]}"
    session = factory()
    assert session.query(Goal).count() == THREADS * WRITES
    session.close()
