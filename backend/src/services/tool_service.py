"""Tool Registry CRUD + Tool Execution Engine.

Provides tool registration, built-in tool executors (file_read, file_search,
git_diff, test_runner), permission enforcement, and tool_call logging.
"""

import glob
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.tool import ToolCallRecord, ToolDefinition


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
]


def _file_read(path: str, cwd: str = ".") -> Dict[str, Any]:
    """Read a file and return its contents."""
    full_path = path if os.path.isabs(path) else os.path.join(cwd, path)
    if not os.path.exists(full_path):
        return {"success": False, "result": f"File not found: {path}"}
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "result": content}
    except Exception as e:
        return {"success": False, "result": f"Error reading file: {str(e)}"}


def _file_search(pattern: str, directory: Optional[str] = None, cwd: str = ".") -> Dict[str, Any]:
    """Search for files matching a glob pattern."""
    search_dir = directory or cwd
    search_dir = search_dir if os.path.isabs(search_dir) else os.path.join(cwd, search_dir)
    try:
        matches = glob.glob(pattern, root_dir=search_dir, recursive=True)
        matches.sort()
        result = f"Found {len(matches)} file(s):\n" + "\n".join(matches[:50])
        if len(matches) > 50:
            result += f"\n... and {len(matches) - 50} more"
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "result": f"Search error: {str(e)}"}


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


def _test_runner(command: str, cwd_path: Optional[str] = None, cwd: str = ".") -> Dict[str, Any]:
    """Execute a test command and return results."""
    work_dir = cwd_path or cwd
    work_dir = work_dir if os.path.isabs(work_dir) else os.path.join(cwd, work_dir)
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=120,
            cwd=work_dir,
        )
        output = result.stdout[:5000] or "(no output)"
        if result.stderr:
            output += f"\n\n[stderr]:\n{result.stderr[:2000]}"
        return {
            "success": result.returncode == 0,
            "result": output,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "result": "Test timed out (>120s)"}
    except Exception as e:
        return {"success": False, "result": f"Test runner error: {str(e)}"}


TOOL_EXECUTORS: Dict[str, Callable] = {
    "file_read": _file_read,
    "file_search": _file_search,
    "git_diff": _git_diff,
    "test_runner": _test_runner,
}


class ToolExecutor:
    def __init__(self, project_root: str = "."):
        self._project_root = project_root

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
        if agent:
            allowed = agent.get_allowed_tools()
            if allowed and tool_name not in allowed:
                raise ToolNotAllowedError(
                    f"Agent '{agent.name}' is not allowed to use tool '{tool_name}'"
                )

        tool_def = (
            db.query(ToolDefinition)
            .filter(ToolDefinition.name == tool_name, ToolDefinition.is_enabled == True)
            .first()
        )
        if not tool_def:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found or disabled")

        executor_fn = TOOL_EXECUTORS.get(tool_name)
        if not executor_fn:
            raise ToolNotFoundError(f"No executor registered for tool '{tool_name}'")

        call_record = ToolCallRecord(
            id=str(uuid.uuid4()),
            goal_id=goal_id,
            task_id=task_id,
            agent_id=agent_id,
            worker_id=worker_id,
            tool_name=tool_name,
            status="started",
        )
        call_record.set_tool_input(arguments)
        db.add(call_record)
        db.flush()

        start_ts = time.time()
        try:
            result = executor_fn(**arguments)
        except Exception as e:
            call_record.status = "failed"
            call_record.error_message = str(e)
            call_record.latency_ms = int((time.time() - start_ts) * 1000)
            db.commit()
            return call_record

        elapsed_ms = int((time.time() - start_ts) * 1000)
        call_record.status = "completed" if result.get("success") else "failed"
        call_record.tool_output = result.get("result", "")
        call_record.latency_ms = elapsed_ms
        if not result.get("success"):
            call_record.error_message = result.get("result", "Unknown error")
        db.commit()
        return call_record


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
