"""Tool Registry CRUD + Tool Execution Engine.

Provides tool registration, built-in tool executors (file_read, file_search,
git_diff, test_runner), permission enforcement, and tool_call logging.
"""

import glob
import hashlib
import json
import os
import shlex
import subprocess
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.tool import ToolCallRecord, ToolDefinition
from src.models.workspace import Artifact, Goal, WorkspaceCheckpoint
from src.models.handoff import WorkerSession
from src.core.config import settings
from src.services.sandbox_service import SandboxRunner, get_sandbox_runner
from src.services.security_service import redact_data, redact_text


class ToolServiceError(Exception):
    pass


class ToolNotAllowedError(ToolServiceError):
    pass


class ToolNotFoundError(ToolServiceError):
    pass


BUILTIN_TOOLS = [
    {
        "name": "file_read",
        "display_name": "文件读取",
        "description": "读取指定文件的内容",
        "category": "文件操作",
        "risk_level": "low",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要读取的文件路径（相对于项目根目录或绝对路径）"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "file_search",
        "display_name": "文件搜索",
        "description": "在目录中搜索匹配模式的文件",
        "category": "文件操作",
        "risk_level": "low",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "glob 匹配模式，如 *.py, **/*.tsx"},
                "dir": {"type": "string", "description": "搜索目录，默认为当前目录"},
            },
            "required": ["pattern"],
        },
    },
    {"name": "glob_search", "display_name": "Glob 搜索", "description": "按 glob 在工作区搜索文件", "category": "文件操作", "risk_level": "low", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "dir": {"type": "string"}}, "required": ["pattern"]}},
    {"name": "workspace_list", "display_name": "工作区列表", "description": "列出工作区内文件", "category": "文件操作", "risk_level": "low", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}},
    {"name": "directory_create", "display_name": "创建目录", "description": "在工作区内创建目录", "category": "文件操作", "risk_level": "medium", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "file_create", "display_name": "创建文件", "description": "仅在文件不存在时创建普通文件", "category": "文件操作", "risk_level": "medium", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "file_write", "display_name": "文件写入", "description": "创建或完全写入工作区内普通文件", "category": "文件操作", "risk_level": "medium", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "file_patch", "display_name": "文件补丁", "description": "用精确文本替换修改工作区内文件", "category": "文件操作", "risk_level": "medium", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}, "expected_checksum": {"type": "string", "description": "可选的修改前 SHA-256，用于检测并发修改"}}, "required": ["path", "old_text", "new_text"]}},
    {"name": "file_delete", "display_name": "删除文件", "description": "删除工作区内文件；必须提供 approved=true", "category": "文件操作", "risk_level": "high", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "approved": {"type": "boolean"}}, "required": ["path", "approved"]}},
    {"name": "checkpoint_create", "display_name": "创建检查点", "description": "保存文件当前内容以便当前 Task 回滚", "category": "状态", "risk_level": "low", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "checkpoint_restore", "display_name": "恢复检查点", "description": "恢复当前 Task 指定文件的最新检查点", "category": "状态", "risk_level": "medium", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "terminal_execute", "display_name": "终端执行", "description": "在受控工作区内执行允许的开发命令", "category": "执行", "risk_level": "medium", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "cwd": {"type": "string"}}, "required": ["command"]}},
    {"name": "lint_run", "display_name": "Lint", "description": "运行白名单 lint 命令", "category": "测试", "risk_level": "low", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "cwd": {"type": "string"}}, "required": ["command"]}},
    {"name": "typecheck_run", "display_name": "类型检查", "description": "运行白名单类型检查命令", "category": "测试", "risk_level": "low", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "cwd": {"type": "string"}}, "required": ["command"]}},
    {"name": "build_run", "display_name": "构建", "description": "运行白名单构建命令", "category": "测试", "risk_level": "medium", "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "cwd": {"type": "string"}}, "required": ["command"]}},
    {
        "name": "git_diff",
        "display_name": "Git 差异",
        "description": "获取 git 工作树的差异",
        "category": "代码",
        "risk_level": "low",
        "parameters": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "比较的 git ref，默认 HEAD"},
                "file": {"type": "string", "description": "指定文件路径，不指定则返回所有变更"},
            },
            "required": [],
        },
    },
    {
        "name": "test_runner",
        "display_name": "测试运行",
        "description": "运行测试命令并返回结果",
        "category": "测试",
        "risk_level": "medium",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的测试命令"},
                "cwd": {"type": "string", "description": "工作目录，默认为项目根目录"},
            },
            "required": ["command"],
        },
    },
    {"name": "git_status", "display_name": "Git 状态", "description": "读取工作区 Git 状态", "category": "代码", "risk_level": "low", "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "git_log", "display_name": "Git 日志", "description": "读取最近 Git 提交", "category": "代码", "risk_level": "low", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}},
    {"name": "artifact_register", "display_name": "登记产物", "description": "登记工作区中已生成的产物", "category": "状态", "risk_level": "low", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "type": {"type": "string"}}, "required": ["path"]}},
]


class ToolPolicyError(ToolServiceError):
    pass


def _safe_path(root: str, value: str = ".", *, allow_missing: bool = True) -> str:
    """Resolve a path and prove that it remains under the workspace root."""
    root_path = os.path.realpath(root)
    candidate = value if os.path.isabs(value) else os.path.join(root_path, value)
    resolved = os.path.realpath(candidate)
    if os.path.commonpath([root_path, resolved]) != root_path:
        raise ToolPolicyError("Path escapes the configured workspace root")
    relative = os.path.relpath(resolved, root_path)
    if _is_sensitive_path(relative):
        raise ToolPolicyError("Access to credential and environment paths is denied")
    if not allow_missing and not os.path.exists(resolved):
        raise ToolPolicyError(f"Path does not exist: {value}")
    return resolved


def _is_sensitive_path(relative_path: str) -> bool:
    parts = [part.lower() for part in relative_path.replace("\\", "/").split("/") if part not in {"", "."}]
    blocked_dirs = {".git", ".ssh", ".aws", ".azure", ".gnupg", ".kube"}
    if any(part in blocked_dirs for part in parts):
        return True
    for part in parts:
        if part == ".env" or part.startswith(".env."):
            return True
        if part in {
            ".npmrc", ".pypirc", "credentials", "credentials.json",
            "service-account.json", "id_rsa", "id_ed25519",
        }:
            return True
        if part.endswith((".pem", ".key", ".p12", ".pfx")):
            return True
    return False


def _truncate(text: str) -> str:
    text = redact_text(text)
    if len(text) <= settings.max_tool_output_chars:
        return text
    return text[:settings.max_tool_output_chars] + "\n[output truncated]"


def _classify_command(command: str) -> Dict[str, Any]:
    try:
        parts = shlex.split(command)
    except ValueError:
        return {"allowed": False, "classification": "invalid", "reason": "command_parse_error"}
    if not parts:
        return {"allowed": False, "classification": "invalid", "reason": "empty_command"}
    binary, args = parts[0], parts[1:]
    if binary in {"python", "python3"}:
        allowed_modules = {"pytest", "unittest", "compileall"}
        if len(args) < 2 or args[0] != "-m" or args[1] not in allowed_modules:
            return {
                "allowed": False,
                "classification": "arbitrary_code",
                "reason": "python_entrypoint_not_allowlisted",
            }
    if any(token in command for token in (";", "&&", "||", "`", "$(", ">", "<", "\n", "\r")):
        return {"allowed": False, "classification": "destructive", "reason": "shell_control_operator"}
    lowered = [part.lower() for part in args]
    blocked = {
        "push", "reset", "clean", "rm", "install", "uninstall", "publish",
        "adduser", "sudo", "su", "curl", "wget", "ssh", "scp",
    }
    if any(token in blocked for token in lowered):
        network_tokens = {"push", "install", "publish", "curl", "wget", "ssh", "scp"}
        category = "network_access" if any(token in network_tokens for token in lowered) else "destructive"
        return {"allowed": False, "classification": category, "reason": "blocked_subcommand"}
    if binary in {"python", "python3"}:
        return {"allowed": True, "classification": "safe_build", "reason": "allowlisted_python_module"}
    if binary == "git":
        subcommand = next((part for part in args if not part.startswith("-")), "")
        if subcommand not in {"status", "diff", "log", "show", "rev-parse"}:
            return {
                "allowed": False,
                "classification": "workspace_write",
                "reason": "git_subcommand_not_allowlisted",
            }
        return {"allowed": True, "classification": "safe_read", "reason": "read_only_git"}
    if binary in {"npm", "pnpm", "yarn"}:
        if not args or args[0] not in {"test", "run"}:
            return {
                "allowed": False,
                "classification": "network_access",
                "reason": "package_subcommand_not_allowlisted",
            }
        return {"allowed": True, "classification": "safe_build", "reason": "package_script"}
    if binary in {"pytest", "ruff", "eslint", "tsc"}:
        return {"allowed": True, "classification": "safe_build", "reason": "verification_binary"}
    return {"allowed": False, "classification": "privileged", "reason": "binary_not_allowlisted"}


def _is_safe_command(command: str) -> bool:
    return bool(_classify_command(command)["allowed"])


def _file_read(path: str, cwd: str = ".") -> Dict[str, Any]:
    """Read a file and return its contents."""
    full_path = _safe_path(cwd, path, allow_missing=False)
    if not os.path.exists(full_path):
        return {"success": False, "result": f"File not found: {path}"}
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read(settings.max_tool_output_chars + 1)
        return {"success": True, "result": _truncate(content)}
    except Exception as e:
        return {"success": False, "result": f"Error reading file: {str(e)}"}


def _file_search(pattern: str, directory: Optional[str] = None, cwd: str = ".") -> Dict[str, Any]:
    """Search for files matching a glob pattern on Python 3.9+.

    ``glob.root_dir`` is unavailable in the Python 3.9 backend image. Build an
    absolute pattern instead, then convert safe matches back to paths relative
    to the requested search directory so the Tool Gateway contract stays the
    same across local and Docker runtimes.
    """
    normalized_pattern = pattern.replace("\\", "/")
    if os.path.isabs(pattern) or any(part == ".." for part in normalized_pattern.split("/")):
        raise ToolPolicyError("Glob pattern escapes the configured workspace root")
    search_dir = _safe_path(cwd, directory or ".")
    try:
        absolute_pattern = os.path.join(search_dir, normalized_pattern)
        raw_matches = glob.glob(absolute_pattern, recursive=True)
        matches = []
        for raw_match in raw_matches:
            try:
                safe_match = _safe_path(search_dir, raw_match, allow_missing=False)
            except ToolPolicyError:
                # Do not expose targets reached through a symlink that escapes
                # the selected workspace directory.
                continue
            relative_match = os.path.relpath(safe_match, search_dir).replace(os.sep, "/")
            if relative_match != ".":
                matches.append(relative_match)
        matches = sorted(set(matches))
        result = f"Found {len(matches)} file(s):\n" + "\n".join(matches[:50])
        if len(matches) > 50:
            result += f"\n... and {len(matches) - 50} more"
        return {"success": True, "result": result}
    except ToolPolicyError:
        raise
    except Exception as e:
        return {"success": False, "result": f"Search error: {str(e)}"}


def _workspace_list(path: str = ".", cwd: str = ".") -> Dict[str, Any]:
    target = _safe_path(cwd, path, allow_missing=False)
    if not os.path.isdir(target):
        return {"success": False, "result": f"Not a directory: {path}"}
    entries = sorted(os.listdir(target))[:200]
    return {"success": True, "result": "\n".join(entries)}


def _directory_create(path: str, cwd: str = ".") -> Dict[str, Any]:
    target = _safe_path(cwd, path)
    os.makedirs(target, exist_ok=True)
    return {"success": True, "result": f"Directory ready: {path}", "changed_files": [target]}


def _file_create(path: str, content: str, cwd: str = ".") -> Dict[str, Any]:
    target = _safe_path(cwd, path)
    if os.path.exists(target):
        return {"success": False, "result": f"File already exists: {path}"}
    return _file_write(path, content, cwd)


def _file_delete(path: str, approved: bool = False, cwd: str = ".") -> Dict[str, Any]:
    if not approved:
        raise ToolPolicyError("file_delete requires explicit human approval")
    target = _safe_path(cwd, path, allow_missing=False)
    if not os.path.isfile(target):
        return {"success": False, "result": f"Not a regular file: {path}"}
    os.remove(target)
    return {"success": True, "result": f"Deleted {path}", "changed_files": [target]}


def _file_write(path: str, content: str, cwd: str = ".") -> Dict[str, Any]:
    target = _safe_path(cwd, path)
    if os.path.basename(target).startswith(".env"):
        raise ToolPolicyError("Writing environment files requires human approval")
    encoded = content.encode("utf-8")
    if len(encoded) > settings.max_file_write_bytes:
        raise ToolPolicyError("File write exceeds configured size limit")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(content)
    return {"success": True, "result": f"Wrote {len(encoded)} bytes", "changed_files": [target]}


def _file_patch(
    path: str,
    old_text: str,
    new_text: str,
    expected_checksum: Optional[str] = None,
    cwd: str = ".",
) -> Dict[str, Any]:
    target = _safe_path(cwd, path, allow_missing=False)
    with open(target, "r", encoding="utf-8") as handle:
        content = handle.read()
    actual_checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if expected_checksum and actual_checksum != expected_checksum:
        return {
            "success": False,
            "result": "File changed since it was read; refresh before applying the patch",
            "conflict": "concurrent_modification",
        }
    if content.count(old_text) != 1:
        return {"success": False, "result": "Patch target must occur exactly once"}
    return _file_write(path, content.replace(old_text, new_text, 1), cwd)


def _create_checkpoint(db: Session, goal_id: str, task_id: str, path: str, root: str) -> WorkspaceCheckpoint:
    target = _safe_path(root, path)
    existed = os.path.isfile(target)
    content = None
    checksum = None
    if existed:
        with open(target, "r", encoding="utf-8") as handle:
            content = handle.read()
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    checkpoint = WorkspaceCheckpoint(goal_id=goal_id, task_id=task_id, path=target, existed=existed, content=content, checksum=checksum)
    db.add(checkpoint)
    db.flush()
    return checkpoint


def _checkpoint_create(path: str, *, db: Session, goal_id: str, task_id: str, root: str, **_: Any) -> Dict[str, Any]:
    checkpoint = _create_checkpoint(db, goal_id, task_id, path, root)
    return {"success": True, "result": f"Checkpoint {checkpoint.id} created", "checkpoint_id": checkpoint.id}


def _checkpoint_restore(path: str, *, db: Session, goal_id: str, task_id: str, root: str, **_: Any) -> Dict[str, Any]:
    target = _safe_path(root, path)
    checkpoint = db.query(WorkspaceCheckpoint).filter(
        WorkspaceCheckpoint.goal_id == goal_id, WorkspaceCheckpoint.task_id == task_id, WorkspaceCheckpoint.path == target
    ).order_by(WorkspaceCheckpoint.created_at.desc()).first()
    if not checkpoint:
        return {"success": False, "result": "No checkpoint exists for this task and path"}
    if checkpoint.existed:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(checkpoint.content or "")
    elif os.path.exists(target):
        os.remove(target)
    return {"success": True, "result": f"Restored checkpoint {checkpoint.id}", "changed_files": [target]}


def _git_diff(ref: Optional[str] = None, file: Optional[str] = None, cwd: str = ".") -> Dict[str, Any]:
    """Run git diff and return results."""
    cmd = ["git", "-C", cwd, "diff"]
    if ref:
        cmd.append(ref)
    if file:
        cmd.append("--")
        cmd.append(file)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"success": False, "result": f"Git diff failed: {result.stderr}"}
        output = result.stdout[:5000]
        if not output:
            return {"success": True, "result": "No changes (clean working tree)"}
        return {"success": True, "result": output}
    except subprocess.TimeoutExpired:
        return {"success": False, "result": "Git diff timed out"}
    except FileNotFoundError:
        return {"success": False, "result": "Git not found in PATH"}
    except Exception as e:
        return {"success": False, "result": f"Git diff error: {str(e)}"}


def _git_command(args: List[str], cwd: str) -> Dict[str, Any]:
    try:
        result = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=30)
        output = result.stdout or result.stderr or "(no output)"
        return {"success": result.returncode == 0, "result": _truncate(output), "exit_code": result.returncode}
    except Exception as exc:
        return {"success": False, "result": f"Git command error: {exc}"}


def _git_status(cwd: str = ".") -> Dict[str, Any]:
    return _git_command(["status", "--short"], cwd)


def _git_log(limit: int = 10, cwd: str = ".") -> Dict[str, Any]:
    bounded = max(1, min(int(limit), 50))
    return _git_command(["log", f"-{bounded}", "--oneline"], cwd)


def _artifact_register(path: str, type: str = "file", *, db: Session, goal_id: str, task_id: str, root: str, **_: Any) -> Dict[str, Any]:
    target = _safe_path(root, path, allow_missing=False)
    if not os.path.isfile(target):
        return {"success": False, "result": f"Artifact is not a file: {path}"}
    with open(target, "rb") as handle:
        checksum = hashlib.sha256(handle.read()).hexdigest()
    artifact = Artifact(task_id=task_id, path=target, checksum=checksum, type=type, verification_status="unverified")
    db.add(artifact)
    db.flush()
    return {"success": True, "result": f"Artifact {artifact.id} registered", "artifact_id": artifact.id, "changed_files": [target]}


def _test_runner(command: str, cwd_path: Optional[str] = None, cwd: str = ".", sandbox_runner: Optional[SandboxRunner] = None) -> Dict[str, Any]:
    """Execute a test command and return results."""
    policy = _classify_command(command)
    if not policy["allowed"]:
        raise ToolPolicyError(f"Command violates the workspace execution policy: {policy['reason']}")
    work_dir = _safe_path(cwd, cwd_path or ".", allow_missing=False)
    try:
        if sandbox_runner:
            result = sandbox_runner.run(command, work_dir, settings.tool_timeout_seconds)
        else:
            result = subprocess.run(
                shlex.split(command), shell=False, capture_output=True, text=True,
                timeout=settings.tool_timeout_seconds, cwd=work_dir,
            )
        output = result.stdout or "(no output)"
        if result.stderr:
            output += f"\n\n[stderr]:\n{result.stderr}"
        return {
            "success": result.returncode == 0,
            "result": _truncate(output), "exit_code": result.returncode,
            "command_policy": policy,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "result": f"Test timed out (>{settings.tool_timeout_seconds}s)",
            "exit_code": None,
            "command_policy": policy,
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"Test runner error: {str(e)}",
            "command_policy": policy,
        }


TOOL_EXECUTORS: Dict[str, Callable] = {
    "file_read": _file_read,
    "file_search": _file_search,
    "glob_search": _file_search,
    "git_diff": _git_diff,
    "git_status": _git_status,
    "git_log": _git_log,
    "test_runner": _test_runner,
    "terminal_execute": _test_runner,
    "lint_run": _test_runner,
    "typecheck_run": _test_runner,
    "build_run": _test_runner,
    "workspace_list": _workspace_list,
    "directory_create": _directory_create,
    "file_create": _file_create,
    "file_write": _file_write,
    "file_patch": _file_patch,
    "file_delete": _file_delete,
    "checkpoint_create": _checkpoint_create,
    "checkpoint_restore": _checkpoint_restore,
    "artifact_register": _artifact_register,
}


class ToolExecutor:
    def __init__(self, project_root: str = "."):
        self._project_root = os.path.realpath(project_root)

    async def execute(
        self,
        db: Session,
        tool_name: str,
        arguments: Dict[str, Any],
        goal_id: str,
        task_id: str,
        agent_id: str,
        worker_id: str,
    ) -> ToolCallRecord:
        agent = db.query(AgentStation).filter(AgentStation.id == agent_id).first()
        idempotency_key = None
        if tool_name in {"file_create", "file_write", "file_patch", "file_delete", "directory_create", "checkpoint_restore", "artifact_register"}:
            payload = json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            idempotency_key = hashlib.sha256(f"{task_id}:{tool_name}:{payload}".encode()).hexdigest()
            existing = db.query(ToolCallRecord).filter(
                ToolCallRecord.idempotency_key == idempotency_key,
                ToolCallRecord.status == "completed",
            ).first()
            if existing:
                return existing
        call_record = ToolCallRecord(
            id=str(uuid.uuid4()),
            goal_id=goal_id,
            task_id=task_id,
            agent_id=agent_id,
            worker_id=worker_id,
            tool_name=tool_name,
            idempotency_key=idempotency_key,
            status="started",
        )
        call_record.set_tool_input(redact_data(arguments))
        db.add(call_record)
        db.flush()
        from src.services import log_service
        log_service.create_log(db, {
            "goal_id": goal_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "worker_id": worker_id,
            "event_type": "tool.started",
            "event_status": "started",
            "tool_name": tool_name,
            "output_summary": f"Tool invocation started: {tool_name}",
            "metadata": {"tool_call_id": call_record.id},
        }, commit=False)
        # Preserve evidence of an in-flight side effect if the process exits.
        db.commit()
        db.refresh(call_record)

        if agent and agent.get_allowed_tools() and tool_name not in agent.get_allowed_tools():
            return _deny_tool_call(db, call_record, f"Agent '{agent.name}' is not allowed to use tool '{tool_name}'")

        tool_def = (
            db.query(ToolDefinition)
            .filter(ToolDefinition.name == tool_name, ToolDefinition.is_enabled == True)
            .first()
        )
        if not tool_def:
            return _deny_tool_call(db, call_record, f"Tool '{tool_name}' not found or disabled")

        executor_fn = TOOL_EXECUTORS.get(tool_name)
        if not executor_fn:
            return _deny_tool_call(db, call_record, f"No executor registered for tool '{tool_name}'")

        goal = db.query(Goal).filter(Goal.id == goal_id).first()
        if goal and goal.execution_mode == "dry_run" and tool_name in {"file_create", "file_write", "file_patch", "file_delete", "directory_create", "terminal_execute", "checkpoint_restore"}:
            call_record.status = "denied"
            call_record.error_message = f"{tool_name} is disabled in dry_run mode"
            call_record.set_result(_normalized_tool_result(call_record, {}, error=call_record.error_message))
            db.commit()
            _emit_tool_event(db, call_record)
            return call_record
        worker = db.query(WorkerSession).filter(WorkerSession.id == worker_id).first()
        root = os.path.realpath(
            worker.workspace_scope if worker and worker.workspace_scope else
            (goal.workspace_root if goal and goal.workspace_root else self._project_root)
        )
        try:
            call_args = dict(arguments)
            if "dir" in call_args and "directory" not in call_args:
                call_args["directory"] = call_args.pop("dir")
            call_args["cwd"] = _safe_path(root, call_args.pop("cwd", "."))
            if goal and goal.execution_mode == "sandbox" and tool_name in {"terminal_execute", "test_runner", "lint_run", "typecheck_run", "build_run"}:
                call_args["sandbox_runner"] = get_sandbox_runner(root)
            if tool_name in {"file_create", "file_write", "file_patch", "file_delete"}:
                # Protect every model write even if it forgot to request a
                # checkpoint explicitly. The user can still restore it via tool.
                effective_path = _safe_path(call_args["cwd"], call_args.get("path", ""))
                _create_checkpoint(db, goal_id, task_id, os.path.relpath(effective_path, root), root)
            if tool_name in {"checkpoint_create", "checkpoint_restore", "artifact_register"}:
                call_args.update({"db": db, "goal_id": goal_id, "task_id": task_id, "root": root})
        except ToolPolicyError as exc:
            call_record.status, call_record.error_message = "denied", str(exc)
            call_record.set_result(_normalized_tool_result(call_record, {}, error=str(exc)))
            db.commit()
            _emit_tool_event(db, call_record)
            return call_record
        start_ts = time.time()
        try:
            result = executor_fn(**call_args)
        except Exception as e:
            call_record.status = "denied" if isinstance(e, ToolPolicyError) else "failed"
            call_record.error_message = str(e)
            call_record.latency_ms = int((time.time() - start_ts) * 1000)
            call_record.set_result(_normalized_tool_result(call_record, {}, error=str(e)))
            db.commit()
            _emit_tool_event(db, call_record)
            return call_record

        elapsed_ms = int((time.time() - start_ts) * 1000)
        call_record.status = "completed" if result.get("success") else "failed"
        call_record.tool_output = redact_text(result.get("result", ""))
        call_record.latency_ms = elapsed_ms
        if not result.get("success"):
            call_record.error_message = redact_text(result.get("result", "Unknown error"))
        call_record.set_result(_normalized_tool_result(call_record, result))
        created_artifact_ids = []
        if result.get("artifact_id"):
            created_artifact_ids.append(result["artifact_id"])
        for changed in result.get("changed_files", []):
            try:
                with open(changed, "rb") as handle:
                    checksum = hashlib.sha256(handle.read()).hexdigest()
                duplicate = db.query(Artifact).filter(
                    Artifact.task_id == task_id,
                    Artifact.path == changed,
                    Artifact.checksum == checksum,
                ).first()
                if not duplicate:
                    artifact = Artifact(
                        task_id=task_id,
                        run_id=goal.run_id if goal else None,
                        path=changed,
                        checksum=checksum,
                        type="file",
                        verification_status="unverified",
                    )
                    db.add(artifact)
                    db.flush()
                    created_artifact_ids.append(artifact.id)
            except OSError:
                pass
        db.commit()
        _emit_tool_event(db, call_record)
        for artifact_id in dict.fromkeys(created_artifact_ids):
            log_service.create_log(db, {
                "goal_id": goal_id,
                "task_id": task_id,
                "agent_id": agent_id,
                "worker_id": worker_id,
                "event_type": "artifact.created",
                "event_status": "completed",
                "output_summary": "Workspace Artifact registered",
                "metadata": {"artifact_id": artifact_id, "tool_call_id": call_record.id},
            })
        return call_record


def _normalized_tool_result(call_record: ToolCallRecord, result: Dict[str, Any], error: Optional[str] = None) -> Dict[str, Any]:
    """Persist the stable Tool Gateway contract for every invocation."""
    output = result.get("result", call_record.tool_output or "")
    status = "success" if call_record.status == "completed" else call_record.status
    return {
        "tool_call_id": call_record.id,
        "tool_name": call_record.tool_name,
        "status": status,
        "exit_code": result.get("exit_code", 0 if status == "success" else None),
        "stdout": output if status == "success" else "",
        "stderr": error or (output if status != "success" else ""),
        "changed_files": result.get("changed_files", []),
        "artifacts": result.get("artifacts", []),
        "duration_ms": call_record.latency_ms,
        "truncated": bool(output and output.endswith("[output truncated]")),
        "command_policy": result.get("command_policy"),
    }


def _deny_tool_call(db: Session, call_record: ToolCallRecord, message: str) -> ToolCallRecord:
    call_record.status, call_record.error_message = "denied", message
    call_record.set_result(_normalized_tool_result(call_record, {}, error=message))
    db.commit()
    _emit_tool_event(db, call_record)
    return call_record


def _emit_tool_event(db: Session, call_record: ToolCallRecord) -> None:
    """Persist the authoritative event at the tool boundary itself."""
    try:
        from src.services import log_service
        log_service.create_log(db, {
            "goal_id": call_record.goal_id,
            "task_id": call_record.task_id,
            "agent_id": call_record.agent_id,
            "worker_id": call_record.worker_id,
            "event_type": "tool.completed" if call_record.status == "completed" else "tool.failed",
            "event_status": call_record.status,
            "tool_name": call_record.tool_name,
            "output_summary": (call_record.tool_output or "")[:200],
            "error_message": call_record.error_message,
            "latency_ms": call_record.latency_ms,
            "metadata": {
                "tool_call_id": call_record.id,
                "command_policy": call_record.get_result().get("command_policy"),
            },
        })
    except Exception:
        # A telemetry failure must not hide the primary tool result; the record
        # itself remains durable and can be reconciled later.
        db.rollback()


_singleton_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    global _singleton_executor
    if _singleton_executor is None:
        _singleton_executor = ToolExecutor()
    return _singleton_executor


def seed_builtin_tools(db: Session) -> List[ToolDefinition]:
    """Insert built-in tools if they don't exist yet. Returns created/existing tools."""
    created = []
    for tool_data in BUILTIN_TOOLS:
        existing = db.query(ToolDefinition).filter(ToolDefinition.name == tool_data["name"]).first()
        if existing:
            existing.display_name = tool_data["display_name"]
            existing.description = tool_data["description"]
            existing.category = tool_data["category"]
            existing.risk_level = tool_data["risk_level"]
            existing.set_parameters(tool_data["parameters"])
            created.append(existing)
            continue
        tool_def = ToolDefinition(
            id=str(uuid.uuid4()),
            name=tool_data["name"],
            display_name=tool_data["display_name"],
            description=tool_data["description"],
            category=tool_data["category"],
            risk_level=tool_data["risk_level"],
            is_enabled=True,
        )
        tool_def.set_parameters(tool_data["parameters"])
        db.add(tool_def)
        db.flush()
        created.append(tool_def)
    db.commit()
    return created
