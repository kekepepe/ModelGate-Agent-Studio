# ruff: noqa: E402
"""Execute the required 5x single/sequential/parallel live benchmark."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from live_provider_acceptance import Api, Scenario, run_scenario


MODE_PROMPTS = {
    "single_agent": (
        "Use exactly one Coder in single_agent mode. Fix math_utils.add, update frontend/status.txt "
        "and backend/status.txt to ready, then run pytest and retain real verification evidence."
    ),
    "sequential_multi_agent": (
        "Use sequential_multi_agent. Have dependent Agents fix math_utils.add, then update both status files, "
        "then run an independent verification task with pytest. Do not run branches concurrently."
    ),
    "parallel_multi_agent": (
        "Use parallel_multi_agent. After a minimal plan, update frontend/status.txt and backend/status.txt in "
        "independent Worktrees while fixing math_utils.add in the backend branch, merge deterministically, and run pytest."
    ),
}


def _percentile(values: List[float], percentile: float, digits: int = 2) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return round(ordered[index], digits)


def _quality_gate(workspace: Path, initial_sha: str) -> Dict:
    commands = [
        [sys.executable, "-m", "pytest", "-q"],
        ["git", "diff", "--check", initial_sha],
    ]
    evidence = []
    passed = True
    for command in commands:
        result = subprocess.run(
            command, cwd=workspace, text=True, capture_output=True, timeout=180, check=False,
        )
        evidence.append({
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
        })
        passed = passed and result.returncode == 0
    expected_files = {
        "frontend/status.txt": "ready",
        "backend/status.txt": "ready",
    }
    for relative, expected in expected_files.items():
        content = (workspace / relative).read_text(encoding="utf-8").lower()
        matched = expected in content
        evidence.append({"file": relative, "expected": expected, "matched": matched})
        passed = passed and matched
    return {"passed": passed, "evidence": evidence}


def calculate_cost(result: Dict, pricing: Dict) -> Dict:
    """Calculate Provider cost from persisted per-model usage."""
    total = 0.0
    by_model = {}
    for model_name, usage in result.get("provider_usage", {}).items():
        price = pricing.get(model_name)
        if not isinstance(price, dict):
            raise ValueError(f"Missing pricing for Provider model '{model_name}'")
        try:
            input_rate = float(price["input_per_million"])
            output_rate = float(price["output_per_million"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid pricing for Provider model '{model_name}'") from exc
        if input_rate < 0 or output_rate < 0:
            raise ValueError(f"Negative pricing for Provider model '{model_name}'")
        cost = (
            usage.get("input_tokens", 0) * input_rate
            + usage.get("output_tokens", 0) * output_rate
        ) / 1_000_000
        by_model[model_name] = round(cost, 8)
        total += cost
    if not by_model:
        raise ValueError("No model_call token usage was persisted for cost calculation")
    return {"cost_usd": round(total, 8), "cost_by_model_usd": by_model}


def aggregate(results: List[Dict], runs_per_mode: int) -> Dict:
    modes = {}
    for mode in MODE_PROMPTS:
        runs = [item for item in results if item.get("benchmark_mode") == mode]
        durations = [
            item.get("goal_duration_ms", item.get("execution", {}).get("total_duration_ms", 0))
            for item in runs
        ]
        tokens = [
            sum(usage.get("total_tokens", 0) for usage in item.get("provider_usage", {}).values())
            or item.get("execution", {}).get("total_tokens_used", 0)
            for item in runs
        ]
        costs = [item["cost_usd"] for item in runs if item.get("cost_usd") is not None]
        successes = [item for item in runs if item.get("passed") and item.get("quality_gate", {}).get("passed")]
        verified = [item for item in runs if item.get("verification_passed")]
        modes[mode] = {
            "run_count": len(runs),
            "required_run_count": runs_per_mode,
            "success_rate": round(len(successes) / max(1, len(runs)), 4),
            "verification_pass_rate": round(len(verified) / max(1, len(runs)), 4),
            "duration_p50_ms": _percentile(durations, 0.50),
            "duration_p95_ms": _percentile(durations, 0.95),
            "tokens_p50": _percentile(tokens, 0.50),
            "tokens_total": sum(tokens),
            "cost_p50_usd": _percentile(costs, 0.50, 8) if len(costs) == len(runs) else None,
            "cost_total_usd": round(sum(costs), 8) if runs and len(costs) == len(runs) else None,
            "replan_count": sum(max(0, item.get("plan_version", 1) - 1) for item in runs),
            "handoff_count": sum(item.get("handoff_count", 0) for item in runs),
            "conflict_count": sum(
                1 for item in runs for worktree in item.get("worktrees", [])
                if worktree.get("status") in {"conflict", "failed"}
            ),
            "human_intervention_count": sum(
                item.get("human_intervention_count", 0) for item in runs
            ),
            "final_diff_quality_pass_rate": round(
                sum(1 for item in runs if item.get("quality_gate", {}).get("passed")) / max(1, len(runs)), 4
            ),
        }

    single = modes["single_agent"]
    sequential = modes["sequential_multi_agent"]
    parallel = modes["parallel_multi_agent"]
    multi_success_not_lower = min(sequential["success_rate"], parallel["success_rate"]) >= single["success_rate"]
    net_time_benefit_ms = sequential["duration_p50_ms"] - parallel["duration_p50_ms"]
    coordination_ratio_ok = parallel["tokens_p50"] <= max(1, single["tokens_p50"]) * 1.5
    conflicts_controlled = parallel["conflict_count"] == 0
    recommended = multi_success_not_lower and net_time_benefit_ms > 0 and coordination_ratio_ok and conflicts_controlled
    complete = all(
        item["run_count"] == runs_per_mode
        and item["success_rate"] == 1.0
        and item["verification_pass_rate"] == 1.0
        and item["final_diff_quality_pass_rate"] == 1.0
        and item["cost_total_usd"] is not None
        for item in modes.values()
    )
    return {
        "passed": complete,
        "modes": modes,
        "decision": {
            "multi_agent_recommended": recommended,
            "success_rate_not_lower": multi_success_not_lower,
            "parallel_net_time_benefit_ms": net_time_benefit_ms,
            "coordination_token_budget_ok": coordination_ratio_ok,
            "conflicts_controlled": conflicts_controlled,
            "note": "A recommendation is emitted only when every roadmap condition is satisfied.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runs-per-mode", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument(
        "--pricing-json",
        default=os.environ.get("MODEL_PRICING_JSON"),
        help=(
            "JSON mapping of Provider model name to input_per_million/output_per_million USD; "
            "defaults to MODEL_PRICING_JSON"
        ),
    )
    args = parser.parse_args()
    if args.runs_per_mode < 5:
        raise SystemExit("The release benchmark requires at least five runs per mode.")
    if not args.pricing_json:
        raise SystemExit("The release benchmark requires --pricing-json or MODEL_PRICING_JSON.")
    try:
        pricing = json.loads(args.pricing_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid pricing JSON: {exc}") from exc
    if not isinstance(pricing, dict):
        raise SystemExit("Pricing JSON must be an object keyed by Provider model name.")

    api = Api(args.base_url, args.timeout)
    results = []
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    benchmark_root = args.runs_dir.resolve() / f"multi-agent-benchmark-{run_stamp}"
    benchmark_root.mkdir(parents=True, exist_ok=False)
    try:
        health = api.client.get(f"{api.origin}/health")
        if health.status_code != 200:
            raise SystemExit(f"Backend health check failed: {health.status_code}")
        for mode, prompt in MODE_PROMPTS.items():
            for run_number in range(1, args.runs_per_mode + 1):
                scenario = Scenario(
                    key=f"{mode}-{run_number:02d}",
                    title="Implement and verify the fixed benchmark change",
                    description=prompt,
                    expected_modes=(mode,),
                    expect_workspace_change=True,
                )
                try:
                    result = run_scenario(api, scenario, benchmark_root / scenario.key)
                    result["benchmark_mode"] = mode
                    result["run_number"] = run_number
                    result["quality_gate"] = _quality_gate(
                        Path(result["workspace"]), result["initial_sha"]
                    )
                    result.update(calculate_cost(result, pricing))
                    results.append(result)
                except Exception as exc:
                    results.append({
                        "scenario": scenario.key,
                        "benchmark_mode": mode,
                        "run_number": run_number,
                        "passed": False,
                        "failures": [str(exc)],
                    })
    finally:
        api.close()

    summary = aggregate(results, args.runs_per_mode)
    report = {**summary, "run_root": str(benchmark_root), "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
