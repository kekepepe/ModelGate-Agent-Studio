import os
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.models.workspace import Goal, Task
from src.services import worktree_service


def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def _repo(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "main.py").write_text("value = 1\n")
    _git(tmp_path, "add", "main.py")
    _git(tmp_path, "commit", "-m", "initial")


def test_worktree_isolated_and_removable(db_session, tmp_path):
    _repo(tmp_path)
    goal = Goal(id=str(uuid.uuid4()), title="Parallel", status="running", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Isolated", status="pending")
    db_session.add_all([goal, task])
    db_session.commit()

    record = worktree_service.create_worktree(db_session, goal, task)
    assert record.branch_name.startswith("modelgate/")
    assert record.base_commit_sha
    isolated = os.path.join(record.path, "main.py")
    assert os.path.isfile(isolated)
    with open(isolated, "w", encoding="utf-8") as handle:
        handle.write("value = 2\n")
    assert (tmp_path / "main.py").read_text() == "value = 1\n"

    worktree_service.remove_worktree(db_session, record)
    assert record.status == "removed"
    assert not os.path.exists(record.path)


def test_dirty_workspace_cannot_spawn_parallel_worktree(db_session, tmp_path):
    _repo(tmp_path)
    (tmp_path / "main.py").write_text("dirty\n")
    goal = Goal(id=str(uuid.uuid4()), title="Parallel", status="running", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Isolated", status="pending")
    db_session.add_all([goal, task])
    db_session.commit()
    with pytest.raises(worktree_service.WorktreeError, match="uncommitted"):
        worktree_service.create_worktree(db_session, goal, task)


def test_merge_applies_isolated_diff_without_overwriting_main(db_session, tmp_path):
    _repo(tmp_path)
    goal = Goal(id=str(uuid.uuid4()), title="Parallel", status="running", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Isolated", status="pending")
    db_session.add_all([goal, task])
    db_session.commit()
    record = worktree_service.create_worktree(db_session, goal, task)
    (Path(record.path) / "main.py").write_text("value = 2\n")

    result = worktree_service.merge_worktree(db_session, record)
    assert result["status"] == "merged"
    assert result["changed"] is True
    assert (tmp_path / "main.py").read_text() == "value = 2\n"
    assert record.commit_sha and record.merge_commit_sha


def test_merge_conflict_preserves_worktree_for_resolution(db_session, tmp_path):
    _repo(tmp_path)
    goal = Goal(id=str(uuid.uuid4()), title="Parallel", status="running", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Isolated", status="pending")
    db_session.add_all([goal, task])
    db_session.commit()
    record = worktree_service.create_worktree(db_session, goal, task)
    (Path(record.path) / "main.py").write_text("value = worker\n")
    (tmp_path / "main.py").write_text("value = main\n")
    _git(tmp_path, "add", "main.py")
    _git(tmp_path, "commit", "-m", "main change")

    result = worktree_service.merge_worktree(db_session, record)
    assert result["status"] == "conflict"
    assert record.status == "conflict"
    assert os.path.isdir(record.path)
    assert record.to_dict()["conflict_files"] == ["main.py"]
    assert not (tmp_path / ".git" / "MERGE_HEAD").exists()


def test_two_real_worktrees_write_concurrently_merge_in_order_and_cleanup(db_session, tmp_path):
    _repo(tmp_path)
    (tmp_path / "frontend.txt").write_text("frontend base\n")
    (tmp_path / "backend.txt").write_text("backend base\n")
    _git(tmp_path, "add", "frontend.txt", "backend.txt")
    _git(tmp_path, "commit", "-m", "parallel base")
    goal = Goal(id=str(uuid.uuid4()), title="Parallel", status="running", workspace_root=str(tmp_path))
    tasks = [
        Task(id=str(uuid.uuid4()), goal_id=goal.id, title=name, status="pending", assigned_agent_id=f"agent-{name}")
        for name in ("frontend", "backend")
    ]
    db_session.add_all([goal, *tasks]); db_session.commit()
    records = [worktree_service.create_worktree(db_session, goal, task) for task in tasks]

    # Materialize immutable values on the owning thread. SQLAlchemy entities
    # are session-bound and must not lazy-load through the shared SQLite
    # connection from worker threads.
    worktree_values = [(record.id, record.path) for record in records]

    def write(record_id, record_path, filename, content):
        (Path(record_path) / filename).write_text(content)
        return record_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(write, *worktree_values[0], "frontend.txt", "frontend worker\n"),
            pool.submit(write, *worktree_values[1], "backend.txt", "backend worker\n"),
        ]
        assert {future.result() for future in futures} == {record.id for record in records}

    for record in sorted(records, key=lambda item: item.task_id):
        assert worktree_service.merge_worktree(db_session, record)["status"] == "merged"
    assert (tmp_path / "frontend.txt").read_text() == "frontend worker\n"
    assert (tmp_path / "backend.txt").read_text() == "backend worker\n"
    assert all(record.commit_sha and record.merge_commit_sha for record in records)
    assert len({record.branch_name for record in records}) == 2

    for record in records:
        worktree_service.remove_worktree(db_session, record)
    assert all(record.status == "removed" and not Path(record.path).exists() for record in records)
    assert _branch_list(tmp_path) == []


def _branch_list(root):
    result = subprocess.run(
        ["git", "-C", str(root), "branch", "--list", "modelgate/*"],
        check=True, capture_output=True, text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
