"""Replaceable execution backends for runtime sandbox tool calls.

The tool policy remains the first line of defence.  This module adds a small,
explicit runtime boundary so deployments can use Docker without coupling tool
implementations to Docker, and tests/dev environments can retain local runs.
"""

import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Optional

from src.core.config import settings


class SandboxExecutionError(RuntimeError):
    """Raised when a configured sandbox backend cannot execute a command."""


@dataclass
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str


class SandboxRunner:
    def run(self, command: str, cwd: str, timeout: int) -> SandboxResult:
        raise NotImplementedError


class LocalSandboxRunner(SandboxRunner):
    """Controlled local fallback; callers already validate command and cwd."""

    def run(self, command: str, cwd: str, timeout: int) -> SandboxResult:
        result = subprocess.run(
            shlex.split(command), shell=False, capture_output=True, text=True,
            timeout=timeout, cwd=cwd,
        )
        return SandboxResult(result.returncode, result.stdout, result.stderr)


class DockerSandboxRunner(SandboxRunner):
    """Run a command in a network-isolated container with only its workspace."""

    def __init__(self, workspace_root: str, image: Optional[str] = None):
        self.workspace_root = os.path.realpath(workspace_root)
        self.image = image or settings.sandbox_image

    def run(self, command: str, cwd: str, timeout: int) -> SandboxResult:
        relative_cwd = os.path.relpath(os.path.realpath(cwd), self.workspace_root)
        if relative_cwd == ".." or relative_cwd.startswith(f"..{os.sep}"):
            raise SandboxExecutionError("Sandbox cwd escapes its workspace mount")
        container_cwd = "/workspace" if relative_cwd == "." else f"/workspace/{relative_cwd}"
        docker_command = [
            "docker", "run", "--rm", "--network", "none", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "256",
            "--volume", f"{self.workspace_root}:/workspace:rw", "--workdir", container_cwd,
            self.image, *shlex.split(command),
        ]
        try:
            result = subprocess.run(
                docker_command, shell=False, capture_output=True, text=True, timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise SandboxExecutionError("Docker sandbox is configured but docker is not installed") from exc
        return SandboxResult(result.returncode, result.stdout, result.stderr)


def get_sandbox_runner(workspace_root: str) -> SandboxRunner:
    if settings.sandbox_backend == "docker":
        return DockerSandboxRunner(workspace_root)
    if settings.sandbox_backend == "local":
        return LocalSandboxRunner()
    raise SandboxExecutionError(f"Unsupported sandbox backend: {settings.sandbox_backend}")
