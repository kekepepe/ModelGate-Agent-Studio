import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "multi_agent_benchmark.py"
SPEC = importlib.util.spec_from_file_location("multi_agent_benchmark", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_benchmark_aggregate_requires_complete_repeated_evidence():
    results = []
    for mode in MODULE.MODE_PROMPTS:
        for run in range(5):
            results.append({
                "benchmark_mode": mode,
                "passed": True,
                "verification_passed": True,
                "quality_gate": {"passed": True},
                "execution": {
                    "total_duration_ms": 1000 if mode == "single_agent" else 1200 if mode == "sequential_multi_agent" else 700,
                    "total_tokens_used": 100 if mode == "single_agent" else 120,
                },
                "plan_version": 1,
                "handoff_count": 0,
                "worktrees": [],
                "event_counts": {},
                "cost_usd": 0.01,
                "run_number": run + 1,
            })
    report = MODULE.aggregate(results, 5)
    assert report["passed"] is True
    assert report["decision"]["multi_agent_recommended"] is True
    assert report["modes"]["parallel_multi_agent"]["run_count"] == 5


def test_benchmark_never_recommends_parallel_when_conflicts_exist():
    results = []
    for mode in MODULE.MODE_PROMPTS:
        for run in range(5):
            results.append({
                "benchmark_mode": mode,
                "passed": True,
                "verification_passed": True,
                "quality_gate": {"passed": True},
                "execution": {"total_duration_ms": 1000, "total_tokens_used": 100},
                "plan_version": 1,
                "handoff_count": 0,
                "worktrees": [{"status": "conflict"}] if mode == "parallel_multi_agent" and run == 0 else [],
                "event_counts": {},
                "cost_usd": 0.01,
            })
    report = MODULE.aggregate(results, 5)
    assert report["decision"]["conflicts_controlled"] is False
    assert report["decision"]["multi_agent_recommended"] is False


def test_benchmark_cost_requires_explicit_pricing_for_every_provider_model():
    result = {
        "provider_usage": {
            "planner-model": {"input_tokens": 1000, "output_tokens": 500},
        },
    }
    cost = MODULE.calculate_cost(result, {
        "planner-model": {"input_per_million": 2, "output_per_million": 8},
    })
    assert cost == {"cost_usd": 0.006, "cost_by_model_usd": {"planner-model": 0.006}}
