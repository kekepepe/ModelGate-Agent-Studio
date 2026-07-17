import os
import subprocess
import uuid
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


def test_merge_conflict_preserves_worktree_for_resolution(db_session, tmp_path):
    _repo(tmp_path)
    goal = Goal(id=str(uuid.uuid4()), title="Parallel", status="running", workspace_root=str(tmp_path))
    task = Task(id=str(uuid.uuid4()), goal_id=goal.id, title="Isolated", status="pending")
    db_session.add_all([goal, task])
    db_session.commit()
    record = worktree_service.create_worktree(db_session, goal, task)
    (Path(record.path) / "main.py").write_text("value = worker\n")
    (tmp_path / "main.py").write_text("value = main\n")

    result = worktree_service.merge_worktree(db_session, record)
    assert result["status"] == "conflict"
    assert record.status == "conflict"
    assert os.path.isdir(record.path)
