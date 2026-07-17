from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import engine, Base, SessionLocal, ensure_runtime_v2_schema
from src.routes import agents, router as router_routes, quota as quota_routes, handoffs as handoff_routes, logs as log_routes, goals as goal_routes, tasks as task_routes, workspace as workspace_routes, runtime as runtime_routes, review as review_routes, knowledge as knowledge_routes, models as model_routes, tools as tool_routes, dashboard as dashboard_routes
from src.data.models import MODEL_SEEDS
from src.models.model import Model
from src.models.agent import AgentStation
from src.models import handoff as handoff_models
from src.models import supervisor as supervisor_models
from src.models import tool as tool_models
from src.schemas.model import MODEL_CONTEXT_TOKEN_OPTIONS
from src.services.tool_service import seed_builtin_tools

Base.metadata.create_all(bind=engine)
ensure_runtime_v2_schema()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

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
            "backup_model_ids": ["model-claude-opus"], "allowed_tools": ["file_read", "diff_view"],
            "system_prompt": "审查任务输出，给出具体质量与风险结论。", "allow_handoff": True,
        },
        {
            "id": "default-researcher", "name": "Researcher", "role": "research",
            "description": "收集资料并提炼可行动结论", "default_model_id": "model-kimi-long-context",
            "backup_model_ids": ["model-claude-opus", "model-gpt-4-turbo"], "allowed_tools": ["file_read"],
            "system_prompt": "整理相关资料、来源与行动建议。", "allow_handoff": True,
        },
        {
            "id": "default-summarizer", "name": "Summarizer", "role": "summarizer",
            "description": "压缩上下文并生成任务摘要", "default_model_id": "model-claude-3-haiku",
            "backup_model_ids": ["model-kimi-long-context"], "allowed_tools": [],
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
            # Existing installations should receive newly introduced safe
            # coder tools without modifying any user-created Agent profile.
            coder_seed = next(item for item in defaults if item["id"] == "default-coder")
            coder = db.query(AgentStation).filter(AgentStation.id == "default-coder").first()
            if coder:
                allowed = set(coder.get_allowed_tools())
                changed = set(coder_seed["allowed_tools"]) - allowed
                if changed:
                    coder.set_allowed_tools(sorted(allowed | changed))
                    db.commit()
    finally:
        db.close()


_seed_default_agents()


@app.get("/health")
def health_check():
    return {"status": "ok"}
