# Runtime architecture

`runtime_service` owns the Goal to Task execution pipeline. `verifier_service` evaluates the evidence-backed Completion Gate. The relational database is the source of truth for Workspace state. Persisted ExecutionLog records are delivered to the browser through the runtime Server-Sent Events endpoint.
