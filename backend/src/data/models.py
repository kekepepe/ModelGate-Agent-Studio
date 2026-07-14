# Hard-coded model seed data for MVP
# These will be seeded into the `models` table on app startup.
# In production, models should be configurable via UI/API.

MODEL_SEEDS = [
    {
        "id": "model-claude-opus",
        "provider": "anthropic",
        "model_name": "claude-3-opus-20240229",
        "display_name": "Claude 3 Opus",
        "capability_tags": ["code", "planning", "reasoning", "long_context", "tool_calling"],
        "max_context_tokens": 1048576,
        "cost_level": 5,
        "speed_level": 3,
        "is_enabled": True,
        "is_default": False,
    },
    {
        "id": "model-gpt-4-turbo",
        "provider": "openai",
        "model_name": "gpt-4-turbo-preview",
        "display_name": "GPT-4 Turbo",
        "capability_tags": ["code", "planning", "reasoning", "tool_calling", "vision"],
        "max_context_tokens": 131072,
        "cost_level": 4,
        "speed_level": 3,
        "is_enabled": True,
        "is_default": False,
    },
    {
        "id": "model-deepseek-coder",
        "provider": "deepseek",
        "model_name": "deepseek-coder",
        "display_name": "DeepSeek Coder",
        "capability_tags": ["code", "reasoning", "low_cost"],
        "max_context_tokens": 131072,
        "cost_level": 2,
        "speed_level": 3,
        "is_enabled": True,
        "is_default": False,
    },
    {
        "id": "model-kimi-long-context",
        "provider": "kimi",
        "model_name": "kimi-long-context",
        "display_name": "Kimi Long Context",
        "capability_tags": ["long_context", "reasoning", "summarization"],
        "max_context_tokens": 1048576,
        "cost_level": 3,
        "speed_level": 4,
        "is_enabled": True,
        "is_default": False,
    },
    {
        "id": "model-claude-3-haiku",
        "provider": "anthropic",
        "model_name": "claude-3-haiku-20240307",
        "display_name": "Claude 3 Haiku",
        "capability_tags": ["fast", "low_cost", "summarization"],
        "max_context_tokens": 262144,
        "cost_level": 1,
        "speed_level": 1,
        "is_enabled": True,
        "is_default": False,
    },
    {
        "id": "model-glm-4",
        "provider": "zhipu",
        "model_name": "glm-4",
        "display_name": "GLM-4",
        "capability_tags": ["vision", "tool_calling", "multilingual", "low_cost"],
        "max_context_tokens": 131072,
        "cost_level": 2,
        "speed_level": 2,
        "is_enabled": True,
        "is_default": False,
    },
]


# Role → preferred model IDs (ordered by preference)
ROLE_MODEL_PREFERENCES = {
    "planner": ["model-claude-opus", "model-gpt-4-turbo", "model-kimi-long-context"],
    "coder": ["model-deepseek-coder", "model-claude-opus", "model-gpt-4-turbo"],
    "reviewer": ["model-gpt-4-turbo", "model-claude-opus"],
    "research": ["model-kimi-long-context", "model-claude-opus", "model-gpt-4-turbo"],
    "summarizer": ["model-claude-3-haiku", "model-glm-4", "model-kimi-long-context"],
    "supervisor": ["model-claude-opus", "model-gpt-4-turbo"],
}


# Task type → required capabilities
TASK_TYPE_CAPABILITIES = {
    "planning": ["planning", "reasoning", "long_context"],
    "coding": ["code", "reasoning"],
    "review": ["reasoning"],
    "research": ["long_context", "reasoning"],
    "summarization": ["summarization", "long_context"],
    "supervision": ["planning", "reasoning"],
    "debugging": ["code", "reasoning"],
    "documentation": ["summarization", "reasoning"],
    "testing": ["code", "reasoning"],
    "general": ["reasoning"],
}


# Default scoring weights
DEFAULT_WEIGHTS = {
    "capability_match": 0.25,
    "role_match": 0.20,
    "context_fit": 0.15,
    "cost_fit": 0.15,
    "speed_fit": 0.10,
    "quota_health": 0.10,
    "historical_performance": 0.05,
}


# Quota status → health score (mock until Quota Manager is ready)
QUOTA_HEALTH_SCORES = {
    "normal": 1.0,
    "warning": 0.7,
    "near_limit": 0.4,
    "limited": 0.0,
    "cooldown": 0.0,
    "unknown": 0.8,
}


def get_model_seed(model_id: str) -> dict:
    for m in MODEL_SEEDS:
        if m["id"] == model_id:
            return m
    return None


def list_model_seeds() -> list:
    return MODEL_SEEDS.copy()
