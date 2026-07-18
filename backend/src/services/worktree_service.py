"""Controlled Git worktree lifecycle for parallel coding workers."""
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone

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
    base_commit_sha = _run_git(root, ["rev-parse", base_ref]).stdout.strip()
    branch_name = f"modelgate/{_branch_part(goal.id)}/{_branch_part(task.id)}"
    _run_git(root, ["worktree", "add", "-b", branch_name, target, base_commit_sha])
    record = existing or WorkspaceWorktree(goal_id=goal.id, task_id=task.id, path=target, base_ref=base_ref)
    record.path, record.base_ref = target, base_ref
    record.base_commit_sha, record.branch_name, record.agent_id = base_commit_sha, branch_name, task.assigned_agent_id
    record.status, record.removed_at, record.merged_at = "active", None, None
    record.commit_sha, record.merge_commit_sha, record.merge_output, record.conflict_files = None, None, None, "[]"
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
    if record.branch_name:
        branch = subprocess.run(
            ["git", "-C", workspace_root, "branch", "-D", record.branch_name],
            capture_output=True, text=True, timeout=30,
        )
        if branch.returncode != 0 and "not found" not in (branch.stderr or "").lower():
            raise WorktreeError((branch.stderr or branch.stdout).strip())
    record.status = "removed"
    record.removed_at = datetime.now(timezone.utc)
    db.commit()


def merge_worktree(db: Session, record: WorkspaceWorktree) -> dict:
    """Commit a worker branch, merge it serially, and abort cleanly on conflict."""
    if record.status not in {"active", "conflict"}:
        raise WorktreeError(f"Worktree is not mergeable: {record.status}")
    goal = db.query(Goal).filter(Goal.id == record.goal_id).first()
    if not goal:
        raise WorktreeError("Goal not found for worktree")
    root, target = os.path.realpath(goal.workspace_root or ""), os.path.realpath(record.path)
    _assert_managed_target(target)
    status = _run_git(target, ["status", "--porcelain"]).stdout.strip()
    if status:
        _run_git(target, ["add", "--all"])
        _run_git(target, ["commit", "-m", f"modelgate: complete task {record.task_id}"])
    record.commit_sha = _run_git(target, ["rev-parse", "HEAD"]).stdout.strip()
    if record.commit_sha == record.base_commit_sha:
        record.status = "merged"
        record.merged_at = datetime.now(timezone.utc)
        record.merge_output = "No changes to merge"
        db.commit()
        return {"status": "merged", "changed": False, "message": "No changes to merge"}

    merge = subprocess.run(
        ["git", "-C", root, "merge", "--no-ff", "--no-edit", record.commit_sha],
        capture_output=True, text=True, timeout=60, env=_git_env(),
    )
    if merge.returncode != 0:
        conflicts = subprocess.run(
            ["git", "-C", root, "diff", "--name-only", "--diff-filter=U"],
            capture_output=True, text=True, timeout=30,
        ).stdout.splitlines()
        if not conflicts:
            conflicts = [
                line[3:] for line in _run_git(root, ["status", "--porcelain"]).stdout.splitlines()
                if len(line) > 3
            ]
        subprocess.run(["git", "-C", root, "merge", "--abort"], capture_output=True, text=True, timeout=30)
        record.status = "conflict"
        record.conflict_files = json.dumps(conflicts)
        record.merge_output = (merge.stderr or merge.stdout).strip()
        db.commit()
        return {"status": "conflict", "changed": False, "message": record.merge_output, "conflict_files": conflicts}
    record.status = "merged"
    record.merged_at = datetime.now(timezone.utc)
    record.merge_commit_sha = _run_git(root, ["rev-parse", "HEAD"]).stdout.strip()
    record.merge_output = (merge.stdout or "Worktree branch merged").strip()
    db.commit()
    return {
        "status": "merged", "changed": True, "message": "Worktree branch merged",
        "commit_sha": record.commit_sha, "merge_commit_sha": record.merge_commit_sha,
    }


def _assert_managed_target(target: str) -> None:
    allowed = os.path.realpath(settings.worktree_root)
    if os.path.commonpath([allowed, target]) != allowed:
        raise WorktreeError("Refusing to manage a path outside WORKTREE_ROOT")


def _run_git(root: str, args: list[str]) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            ["git", "-C", root, *args], capture_output=True, text=True, timeout=30, env=_git_env(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorktreeError(f"Git worktree command failed: {exc}") from exc
    if result.returncode != 0:
        raise WorktreeError((result.stderr or result.stdout or "Git worktree command failed").strip())
    return result


def _git_env() -> dict[str, str]:
    return {
        **os.environ,
        "GIT_AUTHOR_NAME": os.environ.get("GIT_AUTHOR_NAME", "ModelGate Runtime"),
        "GIT_AUTHOR_EMAIL": os.environ.get("GIT_AUTHOR_EMAIL", "runtime@modelgate.local"),
        "GIT_COMMITTER_NAME": os.environ.get("GIT_COMMITTER_NAME", "ModelGate Runtime"),
        "GIT_COMMITTER_EMAIL": os.environ.get("GIT_COMMITTER_EMAIL", "runtime@modelgate.local"),
    }


def _branch_part(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
    if not normalized:
        raise WorktreeError("Goal and Task IDs must produce a safe Git branch name")
    return normalized[:48]
