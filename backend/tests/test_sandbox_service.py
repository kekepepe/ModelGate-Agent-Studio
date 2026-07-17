import os
import subprocess

import pytest

from src.services.sandbox_service import DockerSandboxRunner, LocalSandboxRunner, SandboxExecutionError


def test_local_sandbox_runs_in_requested_workspace(tmp_path):
    result = LocalSandboxRunner().run("python -c 'print(123)'", str(tmp_path), 10)
    assert result.returncode == 0
    assert result.stdout.strip() == "123"


def test_docker_sandbox_uses_isolated_workspace_mount(monkeypatch, tmp_path):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, "ok", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    runner = DockerSandboxRunner(str(tmp_path), image="test-image")
    result = runner.run("pytest -q", str(tmp_path), 20)
    assert result.returncode == 0
    command = captured["command"]
    assert command[:5] == ["docker", "run", "--rm", "--network", "none"]
    assert "--cap-drop" in command and "--security-opt" in command and "--pids-limit" in command
    assert f"{os.path.realpath(tmp_path)}:/workspace:rw" in command
    assert captured["kwargs"]["timeout"] == 20


def test_docker_sandbox_rejects_cwd_outside_workspace(tmp_path):
    runner = DockerSandboxRunner(str(tmp_path))
    with pytest.raises(SandboxExecutionError, match="escapes"):
        runner.run("pytest -q", str(tmp_path.parent), 10)
