# ruff: noqa: E402
"""Run the six mandatory live-Provider Runtime acceptance scenarios.

The backend must already be running in live mode with secrets injected into its
process environment. This client never reads or prints a Provider credential.
It creates isolated disposable Git repositories beneath ``--runs-dir`` and
writes a machine-readable report.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
from urllib.parse import urlsplit

import httpx


class AcceptanceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    description: str
    expected_modes: Sequence[str]
    expect_workspace_change: bool = False
    replan_and_handoff: bool = False


SCENARIOS = (
    Scenario(
        "A-direct",
        "Explain the normalize_name function",
        "Read sample.py and explain normalize_name with exact file evidence. Do not modify any file. Use direct mode.",
        ("direct",),
    ),
    Scenario(
        "B-single",
        "Update one README sentence",
        "Use one Coder only. Change 'Status: draft' in README.md to 'Status: acceptance-ready', then show the real Git diff.",
        ("single_agent",),
        True,
    ),
    Scenario(
        "C-coder-verifier",
        "Fix the arithmetic bug and verify it",
        "Fix math_utils.add, run pytest, and require a separate verification step backed by the successful test ToolCallRecord.",
        ("sequential_multi_agent",),
        True,
    ),
    Scenario(
        "D-research-coder-verifier",
        "Read architecture before implementing normalization",
        "First read ARCHITECTURE.md, then implement slugify in sample.py, add or update tests, and verify with a real test command.",
        ("sequential_multi_agent",),
        True,
    ),
    Scenario(
        "E-parallel",
        "Implement isolated frontend and backend status changes",
        "Use parallel_multi_agent with isolated frontend/** and backend/** Worktrees. Update both status files independently, merge them, then verify the unified repository.",
        ("parallel_multi_agent",),
        True,
    ),
    Scenario(
        "F-replan-handoff",
        "Repair a plan assumption and transfer responsibility",
        "Implement a tested safe_divide function. The acceptance runner will invalidate the first plan and inject a quota handoff before execution.",
        ("single_agent", "sequential_multi_agent"),
        True,
        True,
    ),
)


class Api:
    def __init__(self, base_url: str, timeout: float):
        self.api_root = base_url.rstrip("/")
        parsed = urlsplit(self.api_root)
        self.origin = f"{parsed.scheme}://{parsed.netloc}"
        self.client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self.client.close()

    def call(self, method: str, path: str, payload=None):
        response = self.client.request(method, f"{self.api_root}/{path.lstrip('/')}", json=payload)
        if response.status_code >= 400:
            raise AcceptanceError(f"{method} {path} returned {response.status_code}: {response.text[:1000]}")
        body = response.json()
        if not body.get("success", True):
            raise AcceptanceError(f"{method} {path} failed: {json.dumps(body, ensure_ascii=False)[:1000]}")
        return body.get("data", body)


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=path, text=True, capture_output=True, timeout=30, check=False,
    )
    if result.returncode:
        raise AcceptanceError(f"git {' '.join(args)} failed in {path}: {result.stderr.strip()}")
    return result.stdout.strip()


def seed_workspace(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=False)
    (root / "frontend").mkdir()
    (root / "backend").mkdir()
    (root / "tests").mkdir()
    (root / "README.md").write_text("# Acceptance fixture\n\nStatus: draft\n", encoding="utf-8")
    (root / "ARCHITECTURE.md").write_text(
        "Normalization functions are pure, lowercase their input, and replace spaces with hyphens.\n",
        encoding="utf-8",
    )
    (root / "sample.py").write_text(
        "def normalize_name(value: str) -> str:\n    return value.strip().lower()\n",
        encoding="utf-8",
    )
    (root / "backend" / "__init__.py").write_text("", encoding="utf-8")
    (root / "backend" / "math_utils.py").write_text(
        "def add(left: int, right: int) -> int:\n    return left - right\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_math_utils.py").write_text(
        "from backend.math_utils import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )
    (root / "frontend" / "status.txt").write_text("frontend=pending\n", encoding="utf-8")
    (root / "backend" / "status.txt").write_text("backend=pending\n", encoding="utf-8")
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "acceptance@modelgate.local")
    _git(root, "config", "user.name", "ModelGate Acceptance")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "acceptance fixture")
    return _git(root, "rev-parse", "HEAD")


def _active_plan(api: Api, goal_id: str) -> Dict:
    plans = api.call("GET", f"/goals/{goal_id}/plans")
    active = next((item for item in plans if item.get("status") == "active"), None)
    if not active:
        raise AcceptanceError(f"Goal {goal_id} has no active plan")
    return active


def _all_logs(api: Api, goal_id: str) -> List[Dict]:
    items: List[Dict] = []
    page = 1
    while True:
        batch = api.call("GET", f"/logs?goal_id={goal_id}&page={page}&page_size=100")
        items.extend(batch["items"])
        if page >= batch["total_pages"]:
            return items
        page += 1


def _inject_quota_handoff(api: Api, state: Dict) -> str:
    first_task = state["tasks"][0]
    agent = next(item for item in state["agents"] if item["id"] == first_task["assigned_agent_id"])
    model_id = agent["default_model_id"]
    models = api.call("GET", "/models?page=1&page_size=100")["items"]
    model = next(item for item in models if item["id"] == model_id)
    api.call("POST", "/quota/record-usage", {
        "provider": model["provider"],
        "model_id": model_id,
        "model_name": model["model_name"],
        "request_tokens": 0,
        "response_tokens": 0,
        "total_tokens": 0,
    })
    api.call("PATCH", f"/quota/models/{model_id}/status", {
        "quota_status": "limited",
        "reason": "P4 acceptance quota handoff injection",
    })
    return model_id


def _reset_quota(api: Api, model_id: str) -> None:
    api.call("PATCH", f"/quota/models/{model_id}/status", {
        "quota_status": "normal",
        "reason": "P4 acceptance cleanup",
    })


def run_scenario(api: Api, scenario: Scenario, workspace: Path) -> Dict:
    initial_sha = seed_workspace(workspace)
    goal_started = time.perf_counter()
    created = api.call("POST", "/goals", {
        "title": scenario.title,
        "description": scenario.description,
        "execution_mode": "live",
        "workspace_root": str(workspace.resolve()),
        "max_parallel_tasks": 3,
        "budget_tokens": 200000,
        "max_duration_seconds": 3600,
    })
    goal_id = created["goal_id"]
    api.call("POST", f"/goals/{goal_id}/start")
    plan = _active_plan(api, goal_id)
    if plan.get("planner_type") != "model":
        raise AcceptanceError(f"{scenario.key} used {plan.get('planner_type')} instead of the real Planner")
    if plan.get("task_mode") not in scenario.expected_modes:
        raise AcceptanceError(
            f"{scenario.key} planned {plan.get('task_mode')}; expected one of {list(scenario.expected_modes)}"
        )

    if scenario.replan_and_handoff:
        state = api.call("GET", f"/workspace/{goal_id}/state")
        api.call("POST", f"/goals/{goal_id}/replan", {
            "trigger": "context_invalidated",
            "reason": "Acceptance fixture invalidated the first plan assumption.",
            "replace_task_ids": [state["tasks"][0]["id"]],
            "preserve_verified": True,
        })
        plan = _active_plan(api, goal_id)
        if plan["version"] < 2:
            raise AcceptanceError("Replan did not create a new active version")

    api.call("POST", f"/goals/{goal_id}/plans/{plan['version']}/confirm")
    quota_model_id = None
    try:
        if scenario.replan_and_handoff:
            quota_model_id = _inject_quota_handoff(api, api.call("GET", f"/workspace/{goal_id}/state"))
        execution = api.call("POST", f"/runtime/execute/{goal_id}")
        if scenario.replan_and_handoff:
            if execution["status"] != "handoff":
                raise AcceptanceError(f"Quota injection did not produce handoff: {execution['status']}")
            handoffs = api.call("GET", f"/handoffs?goal_id={goal_id}&page_size=100")["items"]
            if not handoffs:
                raise AcceptanceError("Runtime reported handoff without a HandoffRecord")
            api.call("POST", f"/handoffs/{handoffs[0]['id']}/accept", {})
            execution = api.call("POST", f"/runtime/execute/{goal_id}")
    finally:
        if quota_model_id:
            _reset_quota(api, quota_model_id)

    state = api.call("GET", f"/workspace/{goal_id}/state")
    logs = _all_logs(api, goal_id)
    event_types = {item["event_type"] for item in logs}
    final_sha = _git(workspace, "rev-parse", "HEAD")
    dirty = bool(_git(workspace, "status", "--porcelain"))
    changed = final_sha != initial_sha or dirty
    required_events = {
        "plan.generating", "plan.created", "plan.confirmed", "task.ready", "task.assigned",
        "worker.started", "model.streaming", "verification.started", "goal.completed",
    }
    if scenario.expect_workspace_change:
        required_events.update({
            "tool.started", "tool.completed", "artifact.created", "verification.passed",
            "task.completed_verified",
        })
    else:
        required_events.update({"tool.started", "tool.completed", "verification.completed_unverified"})
    missing_events = sorted(required_events - event_types)
    request_ids = sorted({
        (item.get("metadata") or {}).get("provider_request_id")
        for item in logs
        if (item.get("metadata") or {}).get("provider_request_id")
    })
    task_statuses = [item["status"] for item in state["tasks"]]
    event_counts = Counter(item["event_type"] for item in logs)
    provider_usage = {}
    for item in logs:
        if item.get("event_type") != "model_call":
            continue
        metadata = item.get("metadata") or {}
        model_name = metadata.get("provider_model_name")
        if not model_name:
            model_name = f"unmapped:{item.get('model_id') or 'unknown'}"
        usage = item.get("token_usage") or {}
        bucket = provider_usage.setdefault(model_name, {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "call_count": 0,
        })
        bucket["input_tokens"] += usage.get("input_tokens", 0) or 0
        bucket["output_tokens"] += usage.get("output_tokens", 0) or 0
        bucket["total_tokens"] += usage.get("total_tokens", 0) or 0
        bucket["call_count"] += 1
    deterministic_tasks = [
        item for item in state["tasks"] if item.get("task_type") in {"coding", "merge", "verification"}
    ]
    agents_by_id = {item["id"]: item for item in state["agents"]}
    task_roles = [
        agents_by_id.get(item.get("assigned_agent_id"), {}).get("role") for item in state["tasks"]
    ]
    tool_calls = [call for item in state["tasks"] for call in item.get("recent_tool_calls", [])]
    failures = []
    if state["goal"]["status"] != "completed":
        failures.append(f"goal status is {state['goal']['status']}")
    if missing_events:
        failures.append("missing runtime events: " + ", ".join(missing_events))
    if not request_ids:
        failures.append("no real provider request id was persisted")
    if scenario.expect_workspace_change and not changed:
        failures.append("workspace Git state did not change")
    if not scenario.expect_workspace_change and changed:
        failures.append("read-only scenario changed the workspace")
    if scenario.expect_workspace_change and "artifact.created" not in event_types:
        failures.append("no artifact.created event")
    if scenario.expect_workspace_change and not deterministic_tasks:
        failures.append("no deterministic coding/merge/verification Task was planned")
    if scenario.key == "A-direct":
        if len(state["tasks"]) != 1 or any(role in {"coder", "reviewer", "supervisor"} for role in task_roles):
            failures.append(f"direct mode created an unnecessary execution role: {task_roles}")
        if not any(call.get("tool_name") == "file_read" and call.get("status") == "completed" for call in tool_calls):
            failures.append("direct mode has no successful file_read evidence")
    if scenario.key == "B-single":
        if len(state["tasks"]) != 1 or task_roles != ["coder"]:
            failures.append(f"single-agent scenario did not use exactly one Coder: {task_roles}")
    if scenario.key == "C-coder-verifier" and not {"coder", "reviewer"}.issubset(set(task_roles)):
        failures.append(f"Coder -> Verifier roles are incomplete: {task_roles}")
    if scenario.key == "D-research-coder-verifier" and not {"research", "coder", "reviewer"}.issubset(set(task_roles)):
        failures.append(f"Research -> Coder -> Verifier roles are incomplete: {task_roles}")
    if scenario.key in {"C-coder-verifier", "D-research-coder-verifier", "E-parallel", "F-replan-handoff"}:
        if not any(call.get("tool_name") == "test_runner" and call.get("status") == "completed" for call in tool_calls):
            failures.append("no successful test_runner ToolCallRecord")
    if scenario.key == "E-parallel":
        merged = [item for item in state.get("worktrees", []) if item.get("status") == "merged"]
        if len(merged) < 2:
            failures.append("fewer than two Worktrees reached merged")
    if scenario.replan_and_handoff:
        if len(state.get("plan_versions", [])) < 2:
            failures.append("Replan version history is missing")
        if not state.get("handoffs"):
            failures.append("Handoff history is missing")

    return {
        "scenario": scenario.key,
        "goal_duration_ms": int((time.perf_counter() - goal_started) * 1000),
        "goal_id": goal_id,
        "workspace": str(workspace),
        "passed": not failures,
        "failures": failures,
        "planner_type": plan.get("planner_type"),
        "task_mode": plan.get("task_mode"),
        "plan_version": plan.get("version"),
        "goal_status": state["goal"]["status"],
        "task_statuses": task_statuses,
        "task_roles": task_roles,
        "verification_passed": bool(deterministic_tasks) and all(
            item["status"] == "completed_verified" and item.get("verification_status") == "passed"
            for item in deterministic_tasks
        ),
        "initial_sha": initial_sha,
        "final_sha": final_sha,
        "workspace_dirty": dirty,
        "provider_request_ids": request_ids,
        "provider_usage": provider_usage,
        "event_types": sorted(event_types),
        "event_counts": dict(sorted(event_counts.items())),
        "models_used": sorted({item["model_id"] for item in logs if item.get("model_id")}),
        "worktrees": state.get("worktrees", []),
        "handoff_count": len(state.get("handoffs", [])),
        "human_intervention_count": 2 if scenario.replan_and_handoff else 0,
        "multi_agent_metrics": state.get("multi_agent_metrics"),
        "execution": execution,
    }


def run_suite(base_url: str, runs_dir: Path, timeout: float, scenarios: Iterable[Scenario] = SCENARIOS) -> Dict:
    api = Api(base_url, timeout)
    started = time.time()
    results = []
    try:
        health = api.client.get(f"{api.origin}/health")
        if health.status_code != 200:
            raise AcceptanceError(f"Backend health check failed: {health.status_code}")
        run_root = runs_dir.resolve() / time.strftime("provider-acceptance-%Y%m%d-%H%M%S")
        run_root.mkdir(parents=True, exist_ok=False)
        for scenario in scenarios:
            try:
                results.append(run_scenario(api, scenario, run_root / scenario.key))
            except Exception as exc:
                results.append({"scenario": scenario.key, "passed": False, "failures": [str(exc)]})
        return {
            "passed": all(item["passed"] for item in results),
            "base_url": base_url,
            "run_root": str(run_root),
            "duration_ms": int((time.time() - started) * 1000),
            "results": results,
        }
    finally:
        api.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=3600)
    args = parser.parse_args()
    report = run_suite(args.base_url, args.runs_dir, args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
