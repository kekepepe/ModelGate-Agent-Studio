from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.model import Model as ModelORM
from src.schemas.model import DEFAULT_MODEL_CONTEXT_TOKENS, ModelCreate, ModelUpdate, ModelOut, ModelListResponse

router = APIRouter(tags=["models"])


def _success_response(data):
    return {"success": True, "data": data}


def _error_response(code: str, message: str, status_code: int = 400):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error": {"code": code, "message": message}},
    )


@router.get("/models")
def list_models(
    provider: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(ModelORM)

    if provider:
        query = query.filter(ModelORM.provider == provider)
    if is_enabled is not None:
        query = query.filter(ModelORM.is_enabled == is_enabled)
    if search:
        query = query.filter(
            ModelORM.display_name.contains(search)
            | ModelORM.model_name.contains(search)
            | ModelORM.provider.contains(search)
        )

    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    models = query.offset((page - 1) * page_size).limit(page_size).all()

    items = [ModelOut(**m.to_dict()) for m in models]
    return _success_response(
        ModelListResponse(
            items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
        ).model_dump()
    )


@router.get("/models/{model_id}")
def get_model(model_id: str, db: Session = Depends(get_db)):
    model = db.query(ModelORM).filter(ModelORM.id == model_id).first()
    if not model:
        _error_response("NOT_FOUND", f"Model '{model_id}' not found", 404)
    return _success_response(ModelOut(**model.to_dict()).model_dump())


@router.post("/models", status_code=201)
def create_model(data: ModelCreate, db: Session = Depends(get_db)):
    # Check for duplicate display_name
    existing = db.query(ModelORM).filter(ModelORM.display_name == data.display_name).first()
    if existing:
        _error_response("CONFLICT", f"Model with display_name '{data.display_name}' already exists", 409)

    model = ModelORM(
        provider=data.provider,
        model_name=data.model_name,
        display_name=data.display_name,
        max_context_tokens=data.max_context_tokens or DEFAULT_MODEL_CONTEXT_TOKENS,
        cost_level=data.cost_level or 3,
        speed_level=data.speed_level or 3,
        is_enabled=data.is_enabled if data.is_enabled is not None else True,
        is_default=data.is_default if data.is_default is not None else False,
        api_key=data.api_key,
        api_base_url=data.api_base_url,
    )
    if data.capability_tags:
        model.set_capability_tags(data.capability_tags)

    db.add(model)
    db.commit()
    db.refresh(model)
    return _success_response(ModelOut(**model.to_dict()).model_dump())


@router.put("/models/{model_id}")
def update_model(model_id: str, data: ModelUpdate, db: Session = Depends(get_db)):
    model = db.query(ModelORM).filter(ModelORM.id == model_id).first()
    if not model:
        _error_response("NOT_FOUND", f"Model '{model_id}' not found", 404)

    # Check for duplicate display_name if being updated
    if data.display_name is not None:
        existing = (
            db.query(ModelORM)
            .filter(ModelORM.display_name == data.display_name, ModelORM.id != model_id)
            .first()
        )
        if existing:
            _error_response("CONFLICT", f"Model with display_name '{data.display_name}' already exists", 409)

    update_fields = {
        "provider": data.provider,
        "model_name": data.model_name,
        "display_name": data.display_name,
        "max_context_tokens": data.max_context_tokens,
        "cost_level": data.cost_level,
        "speed_level": data.speed_level,
        "is_enabled": data.is_enabled,
        "is_default": data.is_default,
        "api_key": data.api_key,
        "api_base_url": data.api_base_url,
    }
    for field, value in update_fields.items():
        if value is not None:
            setattr(model, field, value)

    if data.capability_tags is not None:
        model.set_capability_tags(data.capability_tags)

    db.commit()
    db.refresh(model)
    return _success_response(ModelOut(**model.to_dict()).model_dump())


@router.delete("/models/{model_id}")
def delete_model(model_id: str, db: Session = Depends(get_db)):
    model = db.query(ModelORM).filter(ModelORM.id == model_id).first()
    if not model:
        _error_response("NOT_FOUND", f"Model '{model_id}' not found", 404)

    db.delete(model)
    db.commit()
    return _success_response({"id": model_id, "deleted": True})


@router.patch("/models/{model_id}/toggle")
def toggle_model(model_id: str, db: Session = Depends(get_db)):
    model = db.query(ModelORM).filter(ModelORM.id == model_id).first()
    if not model:
        _error_response("NOT_FOUND", f"Model '{model_id}' not found", 404)

    model.is_enabled = not model.is_enabled
    db.commit()
    db.refresh(model)
    return _success_response(
        {
            "id": model.id,
            "is_enabled": model.is_enabled,
        }
    )
