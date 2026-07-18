"""Model-driven structured planning with bounded JSON repair attempts."""

import asyncio
import json
from dataclasses import dataclass
from typing import Dict, List

from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.models.agent import AgentStation
from src.models.model import Model
from src.models.workspace import Goal
from src.schemas.planning import ExecutionPlanContract
from src.services import agent_selector_service, context_service, log_service
from src.services.providers.base import ModelRequest
from src.services.providers.provider_factory import get_provider


class ModelPlanningUnavailable(RuntimeError):
    pass


class ModelPlanningFailed(RuntimeError):
    pass


@dataclass
class ModelPlanningResult:
    contract: ExecutionPlanContract
    agents: Dict[str, AgentStation]
    raw_output: str
    repair_records: List[dict]
    model_id: str


class ModelOrchestrator:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max(1, max_attempts)

    def plan(self, db: Session, goal: Goal) -> ModelPlanningResult:
        planner = (
            db.query(AgentStation)
            .filter(AgentStation.role == "planner", AgentStation.is_enabled == True)
            .order_by(AgentStation.created_at.asc())
            .first()
        )
        if not planner:
            raise ModelPlanningUnavailable("No enabled Planner is available")
        model = db.query(Model).filter(
            Model.id == planner.default_model_id,
            Model.is_enabled == True,
        ).first()
        if not model:
            raise ModelPlanningUnavailable("The enabled Planner has no enabled model")

        try:
            provider = get_provider(model=model, execution_mode=goal.execution_mode)
        except Exception as exc:
            raise ModelPlanningUnavailable(str(exc)) from exc

        if goal.execution_mode != "mock" and hasattr(provider, "health_check"):
            health = asyncio.run(provider.health_check(model.model_name))
            if not health.get("healthy"):
                raise ModelPlanningUnavailable(health.get("message") or "Planner model is unhealthy")

        planning_input = self._build_planning_input(db, goal)
        repair_records: List[dict] = []
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": json.dumps(planning_input, ensure_ascii=False)},
        ]
        last_output = ""
        for attempt in range(1, self.max_attempts + 1):
            request = ModelRequest(
                provider=model.provider,
                model=model.id,
                messages=messages,
                temperature=0.1,
                max_tokens=8192,
                metadata={
                    "provider_model_name": model.model_name,
                    "phase": "planning",
                    "goal_id": goal.id,
                    "attempt": attempt,
                },
            )
            try:
                response = asyncio.run(provider.generate(request))
                last_output = response.content
                payload = self._extract_json(last_output)
                contract = ExecutionPlanContract.model_validate(payload)
                agents = self.resolve_agents(db, contract)
                log_service.create_log(db, {
                    "goal_id": goal.id,
                    "agent_id": planner.id,
                    "model_id": model.id,
                    "event_type": "model_call",
                    "event_status": "completed",
                    "input_summary": "Structured ExecutionPlan request",
                    "output_summary": f"Valid plan returned on attempt {attempt}",
                    "token_usage": {
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "total_tokens": response.total_tokens,
                    },
                    "latency_ms": response.latency_ms,
                    "metadata": {"phase": "planning", "attempt": attempt, "task_mode": contract.task_mode},
                })
                return ModelPlanningResult(contract, agents, last_output, repair_records, model.id)
            except (json.JSONDecodeError, ValidationError, ValueError, ModelPlanningFailed) as exc:
                repair_records.append({
                    "attempt": attempt,
                    "error": str(exc),
                    "raw_output": last_output,
                })
                if attempt >= self.max_attempts:
                    break
                messages.extend([
                    {"role": "assistant", "content": last_output},
                    {
                        "role": "user",
                        "content": (
                            "The previous output failed validation. Return a corrected JSON object only. "
                            f"Validation error: {exc}"
                        ),
                    },
                ])
            except Exception as exc:
                repair_records.append({"attempt": attempt, "error": str(exc), "raw_output": last_output})
                break

        log_service.create_log(db, {
            "goal_id": goal.id,
            "agent_id": planner.id,
            "model_id": model.id,
            "event_type": "plan.validated",
            "event_status": "failed",
            "output_summary": f"Model plan failed validation after {len(repair_records)} attempt(s)",
            "error_message": repair_records[-1]["error"] if repair_records else "Unknown planning error",
            "metadata": {"phase": "planning", "repair_records": repair_records},
        })
        error = repair_records[-1]["error"] if repair_records else "No model output"
        failure = ModelPlanningFailed(f"Model plan validation failed: {error}")
        failure.raw_output = last_output
        failure.repair_records = repair_records
        raise failure

    def _build_planning_input(self, db: Session, goal: Goal) -> dict:
        agents = db.query(AgentStation).filter(AgentStation.is_enabled == True).all()
        capabilities = sorted({capability for agent in agents for capability in self._agent_capabilities(agent)})
        allowed_tools = sorted({tool for agent in agents for tool in agent.get_allowed_tools()})
        return {
            "goal": {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "workspace_root": goal.workspace_root,
            },
            "completion_standard": goal.description or goal.title,
            "team_policy": {
                "team_preset": goal.team_preset,
                "prefer_single_agent_for_small_change": True,
                "review_required_for_high_risk": True,
                "max_parallel_tasks": goal.max_parallel_tasks,
            },
            "available_capabilities": capabilities,
            "allowed_tools": allowed_tools,
            "budget": {
                "tokens": goal.budget_tokens,
                "cost_usd": goal.budget_cost_usd,
                "max_duration_seconds": goal.max_duration_seconds,
            },
            "initial_context": context_service.build_planning_context(db, goal),
            "required_decisions": [
                "whether tasks need decomposition",
                "whether tools are required",
                "whether project context is required",
                "whether multiple capabilities are required",
                "whether any tasks are genuinely parallel-safe",
                "whether verification or human approval is required",
            ],
        }

    @staticmethod
    def _system_prompt() -> str:
        schema = ExecutionPlanContract.model_json_schema()
        return (
            "You are the ModelGate Orchestrator. Choose the smallest safe execution path. "
            "Return exactly one JSON object that conforms to the supplied ExecutionPlan schema. "
            "Do not wrap JSON in Markdown. Never invent unavailable capabilities or tools. "
            "Use direct for a simple answer, single_agent for one tool worker, sequential_multi_agent "
            "for dependency-ordered work, and parallel_multi_agent only for isolated low-conflict work. "
            "Every writing task needs deterministic acceptance criteria. High-risk work needs approval "
            "or a downstream verification task. Schema: "
            + json.dumps(schema, ensure_ascii=False)
        )

    @staticmethod
    def _extract_json(content: str) -> dict:
        stripped = content.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        decoder = json.JSONDecoder()
        start = stripped.find("{")
        if start < 0:
            raise json.JSONDecodeError("No JSON object found", stripped, 0)
        payload, _ = decoder.raw_decode(stripped[start:])
        if not isinstance(payload, dict):
            raise ValueError("ExecutionPlan output must be a JSON object")
        return payload

    def resolve_agents(self, db: Session, contract: ExecutionPlanContract) -> Dict[str, AgentStation]:
        resolved: Dict[str, AgentStation] = {}
        for task in contract.tasks:
            resolved[task.client_task_id] = self.resolve_task_agent(db, task)
        return resolved

    def resolve_task_agent(self, db: Session, task) -> AgentStation:
        capabilities = task.required_capabilities or self._task_type_capabilities(task.task_type)
        try:
            selection = agent_selector_service.select_agent(
                db, task_id=task.client_task_id, task_type=task.task_type,
                required_capabilities=capabilities, required_tools=task.required_tools,
                risk_level=task.risk_level, workspace_scope=task.workspace_scope,
                require_model=False, persist=False,
            )
            agent = db.query(AgentStation).filter(AgentStation.id == selection["selected_agent_id"]).one()
        except agent_selector_service.NoEligibleAgentError as exc:
            raise ModelPlanningFailed(
                f"No enabled Agent can satisfy task '{task.client_task_id}': {exc}"
            ) from exc
        return agent

    @classmethod
    def _agent_for_capability(cls, db: Session, capability: str):
        role_by_capability = {
            "planning": "planner",
            "tool_orchestration": "planner",
            "research": "research",
            "data_analysis": "research",
            "code_read": "coder",
            "code_edit": "coder",
            "test": "coder",
            "review": "reviewer",
            "security_review": "reviewer",
            "document_write": "summarizer",
            "direct": "summarizer",
            "supervision": "supervisor",
        }
        role = role_by_capability.get(capability)
        if not role:
            return None
        agent = (
            db.query(AgentStation)
            .filter(AgentStation.role == role, AgentStation.is_enabled == True)
            .order_by(AgentStation.created_at.asc())
            .first()
        )
        if capability == "direct" and not agent:
            return (
                db.query(AgentStation)
                .filter(AgentStation.role == "planner", AgentStation.is_enabled == True)
                .order_by(AgentStation.created_at.asc())
                .first()
            )
        return agent

    @staticmethod
    def _task_type_capabilities(task_type: str) -> List[str]:
        return {
            "direct": ["direct"],
            "planning": ["planning"],
            "research": ["research"],
            "coding": ["code_edit"],
            "verification": ["review"],
            "merge": ["code_edit"],
        }.get(task_type, [])

    @staticmethod
    def _agent_capabilities(agent: AgentStation) -> List[str]:
        return {
            "planner": ["planning", "tool_orchestration"],
            "research": ["research", "data_analysis"],
            "coder": ["code_read", "code_edit", "test"],
            "reviewer": ["review", "security_review"],
            "summarizer": ["direct", "document_write"],
            "supervisor": ["supervision"],
        }.get(agent.role, [])
