"""Agent runtime package (per design §6.3).

V1.0-2: This package exists to host the runtime layer. The explicit state
machine (`GOAL_TRANSITIONS`, `TASK_TRANSITIONS`, `validate_transition`)
currently lives in `src.services.state_machine_service` and is re-exported
here for discoverability. V1.0-4 (Runtime Engine) will move the worker
loop, tool registry, and orchestrator into this package.
"""

from src.services.state_machine_service import (  # noqa: F401
    GOAL_TRANSITIONS,
    TASK_TRANSITIONS,
    InvalidStateTransition,
    install_state_guards,
    transition_goal,
    transition_task,
    validate_transition,
)

__all__ = [
    "GOAL_TRANSITIONS",
    "TASK_TRANSITIONS",
    "InvalidStateTransition",
    "install_state_guards",
    "transition_goal",
    "transition_task",
    "validate_transition",
]
