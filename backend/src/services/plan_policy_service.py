"""Static Multi-Agent benefit and parallel-conflict preflight for a validated plan."""

from itertools import combinations

from src.schemas.planning import ExecutionPlanContract


def analyze(contract: ExecutionPlanContract) -> dict:
    capabilities = sorted({capability for task in contract.tasks for capability in task.required_capabilities})
    parallel_writers = [task for task in contract.tasks if task.parallel_safe and task.writes_workspace]
    conflicts = []
    for left, right in combinations(parallel_writers, 2):
        if not contract._scopes_overlap(left.workspace_scope, right.workspace_scope):
            continue
        conflicts.append({
            "left_task_id": left.client_task_id,
            "right_task_id": right.client_task_id,
            "left_scope": left.workspace_scope,
            "right_scope": right.workspace_scope,
            "merge_strategy_declared": bool(left.merge_strategy and right.merge_strategy),
            "risk": "managed" if left.merge_strategy and right.merge_strategy else "unsafe",
        })
    independent_tasks = [
        task.client_task_id for task in contract.tasks
        if not task.writes_workspace or bool(task.acceptance_criteria)
    ]
    coordination_tasks = [
        task.client_task_id for task in contract.tasks
        if task.task_type in {"planning", "merge", "verification"}
    ]
    multi = contract.task_mode in {"sequential_multi_agent", "parallel_multi_agent"}
    reasons = []
    if len(capabilities) >= 2:
        reasons.append("The plan requires more than one capability.")
    if len(parallel_writers) >= 2 and not any(item["risk"] == "unsafe" for item in conflicts):
        reasons.append("At least two independently verifiable writers can use isolated worktrees.")
    if any(task.risk_level == "high" for task in contract.tasks):
        reasons.append("High-risk work requires independent review or approval.")
    if not multi:
        reasons.append("The smallest safe path does not require Multi-Agent coordination.")
    return {
        "policy": "smallest_safe_team_v1",
        "multi_agent_recommended": multi,
        "reasons": reasons,
        "distinct_capabilities": capabilities,
        "independently_verifiable_task_ids": independent_tasks,
        "parallel_writer_task_ids": [task.client_task_id for task in parallel_writers],
        "conflict_preflight": conflicts,
        "isolation_required": bool(parallel_writers),
        "deterministic_merge_order": [task.client_task_id for task in parallel_writers],
        "coordination_task_ids": coordination_tasks,
        "estimated_coordination_token_upper_bound": len(coordination_tasks) * 1000,
    }
