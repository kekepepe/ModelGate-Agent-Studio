"""Honest coordination-cost and parallel-benefit estimates for one active plan."""

from typing import Dict, List, Optional

from src.models.workspace import ExecutionPlan, PlanTask, Task


COORDINATION_TASK_TYPES = {"planning", "merge", "verification"}
ACTIVE_STATUSES = {"assigned", "running", "handoff"}


def calculate(plan: Optional[ExecutionPlan], plan_tasks: List[PlanTask], tasks: List[Task]) -> Dict:
    mode = plan.task_mode if plan else ("single_agent" if len(tasks) <= 1 else "sequential_multi_agent")
    coordination = [task for task in tasks if task.task_type in COORDINATION_TASK_TYPES]
    productive = [task for task in tasks if task.task_type not in COORDINATION_TASK_TYPES]
    parallel_runtime_ids = {
        task.runtime_task_id for task in plan_tasks if task.parallel_safe and task.runtime_task_id
    }
    parallel = [task for task in tasks if task.id in parallel_runtime_ids]
    parallel_durations = [task.duration_ms or 0 for task in parallel]
    parallel_serial_ms = sum(parallel_durations)
    parallel_observed_ms = max(parallel_durations, default=0)
    potential_parallel_saving_ms = max(0, parallel_serial_ms - parallel_observed_ms)
    coordination_duration_ms = sum(task.duration_ms or 0 for task in coordination)
    coordination_tokens = sum(task.tokens_used or 0 for task in coordination)
    productive_tokens = sum(task.tokens_used or 0 for task in productive)
    estimated_net_time_benefit_ms = potential_parallel_saving_ms - coordination_duration_ms
    total_recorded_duration_ms = sum(task.duration_ms or 0 for task in tasks)
    total_tokens = coordination_tokens + productive_tokens
    parallel_duration_estimate_ms = total_recorded_duration_ms - parallel_serial_ms + parallel_observed_ms
    agent_ids = {task.assigned_agent_id for task in tasks if task.assigned_agent_id}
    active_agent_ids = {
        task.assigned_agent_id for task in tasks
        if task.assigned_agent_id and task.status in ACTIVE_STATUSES
    }
    active_parallelism = sum(1 for task in tasks if task.status == "running")
    return {
        "mode": mode,
        "why_multi_agent": plan.activation_reason if plan else "No persisted ExecutionPlan activation reason is available.",
        "activated_agent_count": len(agent_ids),
        "active_agent_count": len(active_agent_ids),
        "active_parallelism": active_parallelism,
        "coordination_task_count": len(coordination),
        "coordination_tokens": coordination_tokens,
        "productive_tokens": productive_tokens,
        "coordination_token_ratio": round(coordination_tokens / max(1, coordination_tokens + productive_tokens), 4),
        "coordination_duration_ms": coordination_duration_ms,
        "parallel_task_count": len(parallel),
        "single_agent_serial_baseline_ms": parallel_serial_ms,
        "parallel_observed_estimate_ms": parallel_observed_ms,
        "potential_parallel_saving_ms": potential_parallel_saving_ms,
        "estimated_net_time_benefit_ms": estimated_net_time_benefit_ms,
        "benefit_positive": estimated_net_time_benefit_ms > 0,
        "measurement_note": (
            "Time benefit compares recorded parallel Task durations with a serial sum, then subtracts "
            "planning/merge/verification duration. It is an estimate, not an A/B replay of a single Agent."
        ),
        "mode_comparison": {
            "single_agent": {
                "duration_ms": sum(task.duration_ms or 0 for task in productive),
                "tokens": productive_tokens,
                "basis": "Productive Task durations/tokens without recorded coordination work.",
            },
            "sequential_multi_agent": {
                "duration_ms": total_recorded_duration_ms,
                "tokens": total_tokens,
                "basis": "All recorded Task durations summed serially.",
            },
            "parallel_multi_agent": {
                "duration_ms": parallel_duration_estimate_ms,
                "tokens": total_tokens,
                "basis": "Parallel-safe durations collapsed to their maximum; other work remains serial.",
            },
        },
    }
