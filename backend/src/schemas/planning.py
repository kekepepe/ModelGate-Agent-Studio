"""Validated contracts exchanged between an Orchestrator and the Runtime."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


TaskMode = Literal[
    "direct",
    "single_agent",
    "sequential_multi_agent",
    "parallel_multi_agent",
]
TaskType = Literal["direct", "planning", "research", "coding", "verification", "merge"]
RiskLevel = Literal["low", "medium", "high"]

WRITE_TOOLS = {
    "file_create",
    "file_write",
    "file_patch",
    "directory_create",
}


class PlanTaskContract(BaseModel):
    client_task_id: str = Field(..., min_length=1, max_length=100)
    objective: str = Field(..., min_length=1, max_length=4000)
    task_type: TaskType
    required_capabilities: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    acceptance_criteria: List[Dict[str, Any]] = Field(default_factory=list)
    risk_level: RiskLevel = "low"
    parallel_safe: bool = False
    context_query: str = Field("", max_length=4000)
    approval_required: bool = False
    workspace_scope: Optional[str] = Field(None, max_length=2000)
    merge_strategy: Optional[str] = Field(None, max_length=4000)

    @property
    def writes_workspace(self) -> bool:
        return self.task_type in {"coding", "merge"} or bool(WRITE_TOOLS.intersection(self.required_tools))


class ExecutionPlanContract(BaseModel):
    plan_id: Optional[str] = Field(None, min_length=1, max_length=100)
    version: int = Field(1, ge=1)
    task_mode: TaskMode
    goal_summary: str = Field(..., min_length=1, max_length=4000)
    assumptions: List[str] = Field(default_factory=list)
    required_context: List[str] = Field(default_factory=list)
    activation_reason: str = Field(..., min_length=1, max_length=4000)
    tasks: List[PlanTaskContract] = Field(default_factory=list)
    final_acceptance_criteria: List[Dict[str, Any]] = Field(default_factory=list)
    human_approval_points: List[str] = Field(default_factory=list)
    estimated_cost: Dict[str, Any] = Field(default_factory=dict)
    fallback_reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_plan_graph(self):
        task_ids = [task.client_task_id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("Task IDs must be unique within an ExecutionPlan")

        known_ids = set(task_ids)
        for task in self.tasks:
            missing = sorted(set(task.dependencies) - known_ids)
            if missing:
                raise ValueError(
                    f"Task '{task.client_task_id}' has dependencies that do not exist: {', '.join(missing)}"
                )
            if task.client_task_id in task.dependencies:
                raise ValueError(f"Task '{task.client_task_id}' cannot depend on itself")

        self._validate_acyclic_graph()

        if self.task_mode == "direct" and len(self.tasks) > 1:
            raise ValueError("direct mode can contain at most one execution task")
        if self.task_mode == "single_agent" and len(self.tasks) != 1:
            raise ValueError("single_agent mode can contain exactly one execution task")
        if self.task_mode == "parallel_multi_agent":
            parallel_count = sum(task.parallel_safe for task in self.tasks)
            if parallel_count < 2:
                raise ValueError("parallel_multi_agent mode requires at least two parallel-safe tasks")

        for task in self.tasks:
            if task.writes_workspace and not task.acceptance_criteria:
                raise ValueError(
                    f"Workspace-writing task '{task.client_task_id}' requires at least one acceptance criterion"
                )

        self._validate_parallel_scopes()
        self._validate_high_risk_gates()
        return self

    def _validate_acyclic_graph(self) -> None:
        graph = {task.client_task_id: task.dependencies for task in self.tasks}
        visiting = set()
        visited = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError(f"Task dependency graph contains a cycle at '{task_id}'")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in graph[task_id]:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)

    def _validate_parallel_scopes(self) -> None:
        parallel_writers = [task for task in self.tasks if task.parallel_safe and task.writes_workspace]
        for index, left in enumerate(parallel_writers):
            for right in parallel_writers[index + 1 :]:
                if not self._scopes_overlap(left.workspace_scope, right.workspace_scope):
                    continue
                if left.merge_strategy and right.merge_strategy:
                    continue
                raise ValueError(
                    "Parallel workspace-writing tasks "
                    f"'{left.client_task_id}' and '{right.client_task_id}' have overlapping scopes "
                    "without an explicit merge strategy"
                )

    @staticmethod
    def _scopes_overlap(left: Optional[str], right: Optional[str]) -> bool:
        if not left or not right:
            return True
        left_value = left.rstrip("/* ")
        right_value = right.rstrip("/* ")
        return (
            left_value == right_value
            or left_value.startswith(f"{right_value}/")
            or right_value.startswith(f"{left_value}/")
        )

    def _validate_high_risk_gates(self) -> None:
        approval_points = set(self.human_approval_points)
        dependencies = {task.client_task_id: set(task.dependencies) for task in self.tasks}
        reviewer_tasks = [task for task in self.tasks if task.task_type == "verification"]

        def reviewer_covers(task_id: str) -> bool:
            for reviewer in reviewer_tasks:
                pending = list(reviewer.dependencies)
                seen = set()
                while pending:
                    dependency = pending.pop()
                    if dependency == task_id:
                        return True
                    if dependency in seen:
                        continue
                    seen.add(dependency)
                    pending.extend(dependencies.get(dependency, set()))
            return False

        for task in self.tasks:
            if task.risk_level != "high":
                continue
            if task.approval_required or task.client_task_id in approval_points or reviewer_covers(task.client_task_id):
                continue
            raise ValueError(
                f"High-risk task '{task.client_task_id}' requires a human approval point or downstream Reviewer"
            )


class PlanChangeContract(BaseModel):
    change_type: Literal["created", "replan", "user_edit", "runtime_edit"] = "created"
    reason: str = Field(..., min_length=1, max_length=4000)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    retained_task_ids: List[str] = Field(default_factory=list)
    cancelled_task_ids: List[str] = Field(default_factory=list)
    added_task_ids: List[str] = Field(default_factory=list)
    replaced_task_ids: List[str] = Field(default_factory=list)


DecisionAction = Literal[
    "complete",
    "revise_current_task",
    "replan_graph",
    "handoff",
    "ask_user",
    "blocked",
]


class RuntimeDecisionContract(BaseModel):
    action: DecisionAction
    reason: str = Field(..., min_length=1, max_length=4000)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    task_id: Optional[str] = None


class ReplanRequest(BaseModel):
    trigger: Literal[
        "tool_failure",
        "verification_failure",
        "context_invalidated",
        "workspace_conflict",
        "budget_pressure",
        "user_change",
        "handoff_context_missing",
        "supervisor_review",
        "manual",
    ] = "manual"
    reason: str = Field(..., min_length=1, max_length=4000)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    replace_task_ids: List[str] = Field(default_factory=list)
    plan: Optional[ExecutionPlanContract] = None
    preserve_verified: bool = True

    @model_validator(mode="after")
    def require_replan_scope(self):
        if self.plan is None and not self.replace_task_ids and self.trigger not in {
            "verification_failure",
            "supervisor_review",
        }:
            raise ValueError("Replan requires a replacement Plan or at least one Task to replace")
        return self
