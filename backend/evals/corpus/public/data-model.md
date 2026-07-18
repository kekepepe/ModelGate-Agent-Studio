# Data model

`execution_plans` stores immutable versioned plans. `tool_call_records` stores real tool invocations. Its `idempotency_key` prevents duplicate side effects. `workspace_worktrees` records the worker `commit_sha`, resulting `merge_commit_sha`, branch, task, agent, merge output and conflict files.
