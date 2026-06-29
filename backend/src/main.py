from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import engine, Base, SessionLocal
from src.routes import agents, router as router_routes, quota as quota_routes, handoffs as handoff_routes
from src.data.models import MODEL_SEEDS
from src.models.model import Model
from src.models import handoff as handoff_models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix=settings.api_v1_prefix)
app.include_router(router_routes.router, prefix=settings.api_v1_prefix)
app.include_router(quota_routes.router, prefix=settings.api_v1_prefix)
app.include_router(handoff_routes.router, prefix=settings.api_v1_prefix)


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


@app.get("/health")
def health_check():
    return {"status": "ok"}
