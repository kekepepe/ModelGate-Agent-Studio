import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import SessionLocal
from src.core.migrations import upgrade_database
from src.routes import agents, router as router_routes, quota as quota_routes, handoffs as handoff_routes, logs as log_routes, goals as goal_routes, tasks as task_routes, workspace as workspace_routes, runtime as runtime_routes, review as review_routes, knowledge as knowledge_routes, models as model_routes, tools as tool_routes, dashboard as dashboard_routes
from src.data.models import MODEL_SEEDS
from src.models.model import Model
from src.models.agent import AgentStation
from src.models import handoff as handoff_models  # noqa: F401 - registers mapped tables
from src.models import selection as selection_models  # noqa: F401 - registers mapped tables
from src.models import supervisor as supervisor_models  # noqa: F401 - registers mapped tables
from src.models import tool as tool_models  # noqa: F401 - registers mapped tables
from src.providers.litellm_provider import LiteLLMProvider as _LiteLLMProvider
from src.providers.mock_provider import MockProvider as _MockProvider
from src.schemas.model import MODEL_CONTEXT_TOKEN_OPTIONS
from src.services.tool_service import seed_builtin_tools
from src.services.state_machine_service import install_state_guards
from src.middleware.request_security import RequestBoundaryMiddleware

logger = logging.getLogger(__name__)


def _init_provider() -> object:
    """Pick the active LLM provider from `MODEL_GATE_EXECUTION_MODE`.

    Per design §6.5 / §2.2: a real deployment without a configured key must
    fail visibly instead of silently falling back to a mock. We do not
    auto-construct `LiteLLMProvider` here; we just verify the import path
    and surface the active mode in the startup log.
    """
    if settings.execution_mode == "mock":
        logger.info("Provider: MockProvider (MODEL_GATE_EXECUTION_MODE=mock)")
        return _MockProvider()
    provider = _LiteLLMProvider()
    if not provider.api_key:
        logger.warning(
            "LiteLLMProvider initialised WITHOUT PROVIDER_API_KEY. "
            "Real LLM calls will fail loudly. Set PROVIDER_API_KEY or "
            "switch to MODEL_GATE_EXECUTION_MODE=mock for offline work."
        )
    else:
        logger.info("Provider: LiteLLMProvider (key is set, ready)")
    return provider


install_state_guards()
upgrade_database()
_provider = _init_provider()  # noqa: F841 - eager init to surface config errors at startup

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(RequestBoundaryMiddleware)

app.add_middleware(
    CORSMiddleware,
    # Permit the documented Vite port and an alternate local QA port. Keeping
    # this explicit avoids opening browser API access beyond local development.
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix=settings.api_v1_prefix)
app.include_router(router_routes.router, prefix=settings.api_v1_prefix)
app.include_router(quota_routes.router, prefix=settings.api_v1_prefix)
app.include_router(handoff_routes.router, prefix=settings.api_v1_prefix)
app.include_router(log_routes.router, prefix=settings.api_v1_prefix)
app.include_router(goal_routes.router, prefix=settings.api_v1_prefix)
app.include_router(task_routes.router, prefix=settings.api_v1_prefix)
app.include_router(workspace_routes.router, prefix=settings.api_v1_prefix)
app.include_router(runtime_routes.router, prefix=settings.api_v1_prefix)
app.include_router(review_routes.router, prefix=settings.api_v1_prefix)
app.include_router(knowledge_routes.router, prefix=settings.api_v1_prefix)
app.include_router(model_routes.router, prefix=settings.api_v1_prefix)
app.include_router(tool_routes.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_routes.router, prefix=settings.api_v1_prefix)


def _seed_models():
    """Seed model data if the models table is empty."""
    db = SessionLocal()
    try:
        count = db.query(Model).count()
        if count == 0:
            for seed in MODEL_SEEDS:
                model = Model(
                    id=seed["id"],
                    provider=seed["provider"],
                    model_name=seed["model_name"],
                    display_name=seed["display_name"],
                    max_context_tokens=seed["max_context_tokens"],
                    cost_level=seed["cost_level"],
                    speed_level=seed["speed_level"],
                    is_enabled=seed["is_enabled"],
                    is_default=seed["is_default"],
                )
                model.set_capability_tags(seed["capability_tags"])
                db.add(model)
            db.commit()
    finally:
        db.close()


_seed_models()


def _normalize_model_context_windows():
    """Move legacy context values onto the supported product tiers.

    Handoff thresholds are stored as concrete token counts for runtime
    compatibility, so preserve each Agent's old trigger ratio while its default
    model is moved to a new tier.
    """
    db = SessionLocal()
    try:
        changed = False
        for model in db.query(Model).all():
            if model.max_context_tokens in MODEL_CONTEXT_TOKEN_OPTIONS:
                continue
            old_context = model.max_context_tokens
            new_context = min(MODEL_CONTEXT_TOKEN_OPTIONS, key=lambda tier: abs(tier - old_context))
            for agent in db.query(AgentStation).filter(
                AgentStation.default_model_id == model.id,
                AgentStation.handoff_threshold_tokens.is_not(None),
            ):
                agent.handoff_threshold_tokens = round(
                    new_context * agent.handoff_threshold_tokens / old_context
                )
            model.max_context_tokens = new_context
            changed = True
        if changed:
            db.commit()
    finally:
        db.close()


_normalize_model_context_windows()


def _seed_tools():
    db = SessionLocal()
    try:
        seed_builtin_tools(db)
    finally:
        db.close()


_seed_tools()


def _seed_default_agents():
    """Create a usable local team for a first-run Workspace experience."""
    defaults = [
        {
            "id": "default-planner", "name": "Planner", "role": "planner",
            "description": "拆解 Goal 并规划执行顺序", "default_model_id": "model-gpt-4-turbo",
            "backup_model_ids": ["model-claude-opus"], "allowed_tools": [],
            "system_prompt": "将用户目标拆成清晰、可执行的任务。", "allow_handoff": False,
        },
        {
            "id": "default-coder", "name": "Coder", "role": "coder",
            "description": "实现代码与技术方案", "default_model_id": "model-deepseek-coder",
            "backup_model_ids": ["model-claude-opus", "model-gpt-4-turbo"],
            "allowed_tools": ["workspace_list", "file_read", "file_search", "glob_search", "directory_create", "file_create", "file_write", "file_patch", "checkpoint_create", "checkpoint_restore", "terminal_execute", "test_runner", "lint_run", "typecheck_run", "build_run", "git_status", "git_log", "git_diff", "artifact_register"],
            "system_prompt": "根据任务描述产出可执行的实现方案或代码。", "allow_handoff": True,
        },
        {
            "id": "default-reviewer", "name": "Reviewer", "role": "reviewer",
            "description": "审查输出质量、风险和遗漏", "default_model_id": "model-gpt-4-turbo",
            "backup_model_ids": ["model-claude-opus"],
            "allowed_tools": ["workspace_list", "file_read", "file_search", "git_diff", "test_runner", "lint_run", "typecheck_run", "build_run"],
            "system_prompt": "审查任务输出，给出具体质量与风险结论。", "allow_handoff": True,
        },
        {
            "id": "default-researcher", "name": "Researcher", "role": "research",
            "description": "收集资料并提炼可行动结论", "default_model_id": "model-kimi-long-context",
            "backup_model_ids": ["model-claude-opus", "model-gpt-4-turbo"],
            "allowed_tools": ["workspace_list", "file_read", "file_search", "glob_search"],
            "system_prompt": "整理相关资料、来源与行动建议。", "allow_handoff": True,
        },
        {
            "id": "default-summarizer", "name": "Summarizer", "role": "summarizer",
            "description": "压缩上下文并生成任务摘要", "default_model_id": "model-claude-3-haiku",
            "backup_model_ids": ["model-kimi-long-context"], "allowed_tools": ["workspace_list", "file_read", "file_search"],
            "system_prompt": "将执行信息压缩为清晰的结构化摘要。", "allow_handoff": False,
        },
        {
            "id": "default-supervisor", "name": "Supervisor", "role": "supervisor",
            "description": "审查 Goal 是否完成并生成结论", "default_model_id": "model-claude-opus",
            "backup_model_ids": ["model-gpt-4-turbo"], "allowed_tools": ["file_read"],
            "system_prompt": "审查全部任务，判断是否达成 Goal 并给出最终结论。", "allow_handoff": False,
        },
    ]
    db = SessionLocal()
    try:
        if db.query(AgentStation).count() == 0:
            for seed in defaults:
                agent = AgentStation(
                    id=seed["id"], name=seed["name"], role=seed["role"], description=seed["description"],
                    default_model_id=seed["default_model_id"], system_prompt=seed["system_prompt"],
                    allow_handoff=seed["allow_handoff"], status="idle", is_enabled=True,
                    max_steps_per_task=10, max_tool_calls_per_task=20,
                    max_tokens_per_task=32000, max_duration_seconds=900, max_consecutive_failures=3,
                )
                agent.set_backup_model_ids(seed["backup_model_ids"])
                agent.set_allowed_tools(seed["allowed_tools"])
                db.add(agent)
            db.commit()
        else:
            # Refresh only built-in profiles and preserve every user-created
            # Agent. Safe additions are unioned so local customizations remain.
            changed_any = False
            for seed in defaults:
                agent = db.query(AgentStation).filter(AgentStation.id == seed["id"]).first()
                if not agent:
                    continue
                allowed = set(agent.get_allowed_tools())
                changed = set(seed["allowed_tools"]) - allowed
                if changed:
                    agent.set_allowed_tools(sorted(allowed | changed))
                    changed_any = True
            if changed_any:
                db.commit()
    finally:
        db.close()


_seed_default_agents()


@app.get("/health")
def health_check():
    return {"status": "ok"}
