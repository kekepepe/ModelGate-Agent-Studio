# API contract

Create a Goal with `POST /api/v1/goals`. Confirm a plan using `POST /api/v1/goals/{goal_id}/plans/{version}/confirm`. Read the aggregate using `GET /api/v1/workspace/{goal_id}/state`. Start asynchronous execution with `POST /api/v1/runtime/start/{goal_id}`.
