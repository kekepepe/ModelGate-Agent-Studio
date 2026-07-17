"""Controlled Git worktree lifecycle for parallel coding workers."""
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.core.config import settings
from src.models.workspace import Goal, Task, WorkspaceWorktree


class WorktreeError(RuntimeError):
    pass


def create_worktree(db: Session, goal: Goal, task: Task, base_ref: str = "HEAD") -> WorkspaceWorktree:
    existing = db.query(WorkspaceWorktree).filter(WorkspaceWorktree.task_id == task.id).first()
    if existing and existing.status == "active" and os.path.isdir(existing.path):
        return existing
    root = os.path.realpath(goal.workspace_root or "")
    if not root or not os.path.isdir(os.path.join(root, ".git")):
        raise WorktreeError("Parallel execution requires a Git workspace root")
    _run_git(root, ["status", "--porcelain"])
    status = _run_git(root, ["status", "--porcelain"]).stdout.strip()
    if status:
        raise WorktreeError("Workspace has uncommitted changes; isolate or commit them before parallel execution")
    target = os.path.realpath(os.path.join(settings.worktree_root, goal.id, task.id))
    allowed = os.path.realpath(settings.worktree_root)
    if os.path.commonpath([allowed, target]) != allowed:
        raise WorktreeError("Invalid worktree target")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    _run_git(root, ["worktree", "add", "--detach", target, base_ref])
    record = existing or WorkspaceWorktree(goal_id=goal.id, task_id=task.id, path=target, base_ref=base_ref)
    record.path, record.base_ref, record.status, record.removed_at = target, base_ref, "active", None
    if not existing:
        db.add(record)
    db.commit()
    return record


def remove_worktree(db: Session, record: WorkspaceWorktree) -> None:
    if record.status == "removed":
        return
    root = db.query(Goal).filter(Goal.id == record.goal_id).first()
    if not root:
        raise WorktreeError("Goal not found for worktree")
    workspace_root = os.path.realpath(root.workspace_root or "")
    target = os.path.realpath(record.path)
    allowed = os.path.realpath(settings.worktree_root)
    if os.path.commonpath([allowed, target]) != allowed:
        raise WorktreeError("Refusing to remove a path outside WORKTREE_ROOT")
    _run_git(workspace_root, ["worktree", "remove", "--force", target])
    if os.path.exists(target):
        shutil.rmtree(target)
    record.status = "removed"
    record.removed_at = datetime.now(timezone.utc)
    db.commit()


def merge_worktree(db: Session, record: WorkspaceWorktree) -> dict:
    """Apply an isolated worker's uncommitted diff back to its clean base.

    The patch is checked before application. A conflict leaves the worktree in
    place for a dedicated resolution task; it never overwrites the main tree.
    """
    if record.status not in {"active", "conflict"}:
        raise WorktreeError(f"Worktree is not mergeable: {record.status}")
    goal = db.query(Goal).filter(Goal.id == record.goal_id).first()
    if not goal:
        raise WorktreeError("Goal not found for worktree")
    root, target = os.path.realpath(goal.workspace_root or ""), os.path.realpath(record.path)
    _assert_managed_target(target)
    patch = _run_git(target, ["diff", "--binary", "HEAD"]).stdout
    if not patch.strip():
        record.status = "merged"
        db.commit()
        return {"status": "merged", "changed": False, "message": "No changes to merge"}
    check = subprocess.run(["git", "-C", root, "apply", "--check", "--3way"], input=patch, capture_output=True, text=True, timeout=30)
    if check.returncode != 0:
        record.status = "conflict"
        db.commit()
        return {"status": "conflict", "changed": False, "message": (check.stderr or check.stdout).strip()}
    apply = subprocess.run(["git", "-C", root, "apply", "--3way"], input=patch, capture_output=True, text=True, timeout=30)
    if apply.returncode != 0:
        record.status = "conflict"
        db.commit()
        return {"status": "conflict", "changed": False, "message": (apply.stderr or apply.stdout).strip()}
    record.status = "merged"
    db.commit()
    return {"status": "merged", "changed": True, "message": "Worktree diff applied"}


def _assert_managed_target(target: str) -> None:
    allowed = os.path.realpath(settings.worktree_root)
    if os.path.commonpath([allowed, target]) != allowed:
        raise WorktreeError("Refusing to manage a path outside WORKTREE_ROOT")


def _run_git(root: str, args: list[str]) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorktreeError(f"Git worktree command failed: {exc}") from exc
    if result.returncode != 0:
        raise WorktreeError((result.stderr or result.stdout or "Git worktree command failed").strip())
    return result
