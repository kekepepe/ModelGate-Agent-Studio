"""Agent runtime package (per design §6.3).

V1.0-2: package entry + state-machine re-export.
V1.0-4: orchestrator + worker-loop re-exports so the design-documented
import path (`from src.runtime import ...`) works end-to-end.

The actual implementation lives in `src.services.*` and is **re-used
in place** rather than moved (V1.0 B path: minimal change, no rewrite).
The re-exports here exist for two reasons:
  1. The new design §6.3 specifies `src.runtime.*` as the discovery path.
  2. Frontend / business code should depend on the `src.runtime` API
     surface, not the internal `src.services.runtime_service` symbol.

When the runtime engine is fully extracted (V1.x > V1.0), these
re-exports will be replaced by direct module references.
"""

# --- state machine (V1.0-2) ---
from src.services.state_machine_service import (  # noqa: F401
    GOAL_TRANSITIONS,
    TASK_TRANSITIONS,
    InvalidStateTransition,
    install_state_guards,
    transition_goal,
    transition_task,
    validate_transition,
)

# --- orchestrator (V1.0-4) ---
# Re-exported by name so callers can write `from src.runtime import execute_goal_pipeline`.
# Wrapped in a try/except to keep the package importable even if a future
# refactor temporarily breaks the runtime_service module.
try:  # pragma: no cover - defensive guard
    from src.services.runtime_service import (  # noqa: F401
        RuntimeError as _RuntimeError,
        GoalNotReadyError,
        TaskNotReadyError,
        ensure_plan_confirmed,
        execute_goal_pipeline,
        execute_task_step,
        get_runtime_status,
        pause_goal_run,
        resume_goal_run,
        stop_goal_run,
    )
except ImportError:  # pragma: no cover
    _RuntimeError = RuntimeError  # type: ignore[assignment,misc]
    GoalNotReadyError = None  # type: ignore[assignment,misc]
    TaskNotReadyError = None  # type: ignore[assignment,misc]
    ensure_plan_confirmed = None  # type: ignore[assignment,misc]
    execute_goal_pipeline = None  # type: ignore[assignment,misc]
    execute_task_step = None  # type: ignore[assignment,misc]
    get_runtime_status = None  # type: ignore[assignment,misc]
    pause_goal_run = None  # type: ignore[assignment,misc]
    resume_goal_run = None  # type: ignore[assignment,misc]
    stop_goal_run = None  # type: ignore[assignment,misc]


# Public surface (per design §6.3)
__all__ = [
    # state machine
    "GOAL_TRANSITIONS",
    "TASK_TRANSITIONS",
    "InvalidStateTransition",
    "install_state_guards",
    "transition_goal",
    "transition_task",
    "validate_transition",
    # orchestrator
    "GoalNotReadyError",
    "TaskNotReadyError",
    "ensure_plan_confirmed",
    "execute_goal_pipeline",
    "execute_task_step",
    "get_runtime_status",
    "pause_goal_run",
    "resume_goal_run",
    "stop_goal_run",
]
