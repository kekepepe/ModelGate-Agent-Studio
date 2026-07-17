"""Model Manager backed availability checks and normalized provider access."""
import asyncio
import time
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.models.model import Model
from src.services.providers.provider_factory import ProviderConfigurationError, get_provider


def check_model_health(db: Session, model_id: str, execution_mode: str = "live") -> Dict[str, Any]:
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise ValueError(f"Model '{model_id}' not found")
    started = time.time()
    try:
        provider = get_provider(model=model, execution_mode=execution_mode)
        if execution_mode == "mock":
            result = {"healthy": True, "message": "Explicit Mock mode"}
        elif hasattr(provider, "health_check"):
            result = asyncio.run(provider.health_check(model.model_name))
        else:
            result = {"healthy": False, "message": "Provider has no health check capability"}
    except ProviderConfigurationError as exc:
        result = {"healthy": False, "message": str(exc)}
    result.update({"model_id": model.id, "provider": model.provider, "execution_mode": execution_mode, "latency_ms": int((time.time() - started) * 1000)})
    return result
